import pytesseract
from PIL import Image

# ⚠️ UPDATE THIS PATH to point to your tesseract.exe file
# Common Windows path: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    # You can use any image with text on it for this test
    # Just make sure the image file is in the same folder
    text = pytesseract.image_to_string(Image.open(r'F:\pybls\exmpl prscrptn\Screenshot 2026-01-18 041837.png'))
    print("--- OCR RESULT ---")
    print(text)
except Exception as e:
    print(f"Error: {e}")