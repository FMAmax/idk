import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import pandas as pd

# Point to Tesseract executable (Windows only)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    """
    Standard preprocessing to make text sharp and remove shadows/noise.
    """
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_medications(text):
    """
    Extract medication lines using multiple detection rules.
    More flexible approach that catches more medicines.
    """
    medications = []
    
    for line in text.splitlines():
        line = line.strip()
        
        # Ignore empty lines and very short lines
        if not line or len(line) < 3:
            continue
        
        # Rule 1: Contains dosage pattern (mg, ml, mcg, g, iu)
        if re.search(r"\b\d+\s?(mg|ml|mcg|g|iu)\b", line.lower()):
            medications.append(line)
        
        # Rule 2: Contains tablet/capsule keywords
        elif re.search(r"\b(tab|tablet|cap|capsule|syrup|inj|injection|susp|oint|cream|gel|drop)\b", line.lower()):
            medications.append(line)
        
        # Rule 3: Starts with a number followed by period (prescription list format)
        elif re.match(r"^\d+[\.\)]\s+", line):
            medications.append(line)
        
        # Rule 4: Common medication name patterns (expand as needed)
        elif re.search(r"\b(advil|tylenol|aspirin|ibuprofen|amoxicillin|metformin|cefixime|omeprazole|ketorolac|calcium)\b", line.lower()):
            medications.append(line)
    
    return medications

def parse_prescription_detailed(text):
    """
    Parse extracted medications into structured data.
    """
    medicines = []
    med_lines = extract_medications(text)
    
    for line in med_lines:
        line = line.strip()
        
        # Remove leading numbers (e.g., "1. ")
        clean_line = re.sub(r'^\s*\d+[\.\)]\s*', '', line)
        
        # Extract type
        med_type = "Unknown"
        type_match = re.search(r"\b(Tab|Cap|Syp|Inj|Susp|Oint|Cream|Gel|Drop)", clean_line, re.IGNORECASE)
        if type_match:
            med_type = type_match.group(1)
        
        # Extract dosage
        dosage = "N/A"
        dosage_match = re.search(r"(\d+\s*(?:mg|ml|mcg|g|iu))", clean_line, re.IGNORECASE)
        if dosage_match:
            dosage = dosage_match.group(1)
        
        # Extract medicine name (everything between type and dosage)
        name = clean_line
        if '(' in clean_line:
            name = clean_line.split('(')[0].strip()
        elif type_match:
            name = clean_line[:type_match.start()].strip()
        
        if name and name.lower() not in ['tab', 'cap', 'syp', 'inj']:
            medicines.append({
                "Type": med_type,
                "Medicine Name": name,
                "Dosage/Strength": dosage,
                "Original Text": line
            })
    
    return medicines

# -----------------------------------------------------------------------------
# UI Layout
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Rx Parser", layout="wide")
st.title("💊 Prescription Medicine Extractor")
st.markdown("Upload a prescription to extract medicine names and ignore the noise.")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Prescription Image", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Prescription", use_container_width=True)

with col2:
    if uploaded_file:
        st.subheader("Extracted Medicines")
        
        if st.button("Extract Medicines"):
            with st.spinner("Analyzing..."):
                # 1. Preprocess
                processed_img = preprocess_image(image)
                
                # 2. Run OCR
                raw_text = pytesseract.image_to_string(processed_img, config='--psm 6 -l eng')
                
                # 3. Parse Logic (Using improved multi-rule extraction)
                extracted_data = parse_prescription_detailed(raw_text)
                
                if extracted_data:
                    df = pd.DataFrame(extracted_data)
                    st.table(df[["Type", "Medicine Name", "Dosage/Strength"]])
                    
                    # Option to download CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download as CSV", csv, "medicines.csv", "text/csv")
                else:
                    st.warning("No medicines found. Try uploading a clearer image.")
                    with st.expander("See Raw OCR Output"):
                        st.text(raw_text)