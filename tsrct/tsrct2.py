from flask import Flask, request, render_template
from PIL import Image
import pytesseract
import re
import os

app = Flask(__name__)

# Configure Tesseract path for macOS
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_medications(text):
    """Extract medication-related lines from OCR text"""
    medications = []

    for line in text.splitlines():
        line = line.strip()

        # Ignore empty lines
        if not line:
            continue

        # Rule 1: dosage pattern (mg, ml, mcg, g, iu)
        if re.search(r"\b\d+\s?(mg|ml|mcg|g|iu)\b", line.lower()):
            medications.append(line)

        # Rule 2: tablet/capsule keywords
        elif re.search(r"\b(tab|tablet|cap|capsule|syrup|inj|injection)\b", line.lower()):
            medications.append(line)

        # Rule 3: Common medication patterns (optional, can be expanded)
        elif re.search(r"\b(advil|tylenol|aspirin|ibuprofen|amoxicillin|metformin)\b", line.lower()):
            medications.append(line)

    return medications

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.lower().endswith('.png'):
            try:
                image = Image.open(file.stream).convert("RGB")
                extracted_text = pytesseract.image_to_string(image)
                medications = extract_medications(extracted_text)
                return render_template("result.html",
                                     full_text=extracted_text,
                                     medications=medications)
            except Exception as e:
                return render_template("result.html",
                                     error=f"Error processing image: {str(e)}",
                                     medications=[])
        else:
            return render_template("result.html",
                                 error="Please upload a PNG file only.",
                                 medications=[])

    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=8001)