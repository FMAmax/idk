import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import pandas as pd

# Point to Tesseract executable (Windows only) - Uncomment if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    """
    Advanced preprocessing for photos of documents.
    Uses Adaptive Thresholding to handle shadows and uneven lighting.
    """
    img = np.array(image)
    
    # 1. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # 2. Denoise (removes grainy noise)
    gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    
    # 3. Adaptive Thresholding (Crucial for phone camera photos with shadows)
    # This looks at small neighbors of pixels rather than the whole image
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    return thresh

def parse_prescription(text):
    medicines = []
    lines = text.split('\n')
    
    # Improved Keywords: added variations and made dot optional
    # matches "Cap", "Cap.", "Tab", "Tab.", "Tabs"
    med_types_pattern = r"(Cap|Tab|Syp|Inj|Susp|Oint|Drop|Cream|Gel)s?\.?"

    for line in lines:
        line = line.strip()
        if not line: continue
            
        # Regex Logic:
        # 1. Optional Number at start (e.g., "1.")
        # 2. The Medicine Type (Group 1)
        # 3. The Medicine Name & Dosage (Group 2)
        pattern = f"^\s*(?:\d+[\.\)\s]*)?({med_types_pattern})\s+(.*)"
        
        match = re.search(pattern, line, re.IGNORECASE)
        
        if match:
            med_type = match.group(1).strip()
            rest_of_line = match.group(2).strip()
            
            # --- Dosage Extraction Logic ---
            # Check for dosage in parentheses, e.g., "(400 mg)"
            dosage_match = re.search(r'\((.*?)\)', rest_of_line)
            
            if dosage_match:
                dosage = dosage_match.group(1)
                # Remove the dosage from the name to clean it up
                med_name = rest_of_line.replace(f"({dosage})", "").strip()
            else:
                dosage = "N/A"
                med_name = rest_of_line

            # Clean up leading dots or punctuation from name just in case
            med_name = med_name.lstrip(".:- ")

            medicines.append({
                "Type": med_type, 
                "Medicine Name": med_name,
                "Dosage": dosage
            })
            
    return medicines

st.set_page_config(page_title="Rx Parser", layout="wide")
st.title("💊 Prescription Medicine Extractor (Fixed)")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Prescription", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_container_width=True)

with col2:
    if uploaded_file:
        st.subheader("Results")
        if st.button("Extract Medicines"):
            with st.spinner("Processing..."):
                # 1. Preprocess
                processed_img = preprocess_image(image)
                
                # Debug: Show the processed image so we know what Tesseract sees
                with st.expander("Show Processed Image (Debug)"):
                    st.image(processed_img, caption="Contrast Enhanced", use_container_width=True)

                # 2. OCR
                # --oem 1 uses LSTM (Neural Net) for better accuracy
                # --psm 6 assumes a single block of text
                custom_config = r'--oem 1 --psm 6'
                raw_text = pytesseract.image_to_string(processed_img, config=custom_config)
                
                # Debug: Show raw text to check if 'Cefixime' was read
                with st.expander("Show Raw Text (Debug)"):
                    st.text(raw_text)

                # 3. Parse
                data = parse_prescription(raw_text)
                
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("No medicines found. Please check the 'Processed Image' above. If it's too dark, the OCR cannot read the text.")