import streamlit as st
import pandas as pd
from thefuzz import process
from PIL import Image
import pytesseract
import re  # <--- Added for the new Logic

# -------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="PharmaPrice Assistant", page_icon="💊")
# ⚠️ UPDATE THIS PATH to match your computer
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize Session State
if 'search_input' not in st.session_state:
    st.session_state['search_input'] = ''
if 'ocr_results' not in st.session_state:
    st.session_state['ocr_results'] = [] 

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(r'F:\pybls\csv files\formatted_medicines_v3.csv')
        df_clean = df.drop_duplicates(subset=['brand_name'], keep='first')
        return df, df_clean.set_index('brand_name').to_dict('index')
    except FileNotFoundError:
        return None, None

df, medicines = load_data()

def extract_medications_from_text(text):
    """
    Filters raw OCR text to find lines that look like medications 
    (contain 'mg', 'ml', 'Tab', 'Cap', etc.)
    """
    candidates = []
    
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        line_lower = line.lower()

        if re.search(r"\b\d+\s?(mg|ml|mcg|gm|g|iu)\b", line_lower):
            candidates.append(line)
        
        elif re.search(r"\b(tab|cal|cap|capsule|syr|syrup|inj|injection|supp|susp)\b", line_lower):
            candidates.append(line)
            
    return candidates

st.sidebar.header("📷 Scan Prescription")
uploaded_file = st.sidebar.file_uploader("Upload prescription image:", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.sidebar.image(image, caption='Uploaded Image', use_container_width=True)
        
        if st.sidebar.button("🔍 Analyze Prescription"):
            st.sidebar.write("Processing image...")
            
            raw_text = pytesseract.image_to_string(image)
            
            medication_lines = extract_medications_from_text(raw_text)
            
            if not medication_lines:
                st.sidebar.warning("No medication lines (mg/Tab/Inj) detected.")
            else:
                st.sidebar.info(f"Scanning {len(medication_lines)} potential lines...")
                found_items = []
                
                for line in medication_lines:
                
                    clean_line = re.sub(r'\d+\+\d+\+\d+', '', line) 
                    
                    match_result = process.extractOne(clean_line, medicines.keys())
                    
                    if match_result:
                        best_match, score = match_result
                        if score >= 60:
                            found_items.append(best_match)
                
                if found_items:
                    st.session_state['ocr_results'] = list(set(found_items))
                    st.sidebar.success(f"Matched {len(st.session_state['ocr_results'])} medicines!")
                    st.rerun()
                else:
                    st.sidebar.warning("Text detected, but no matching brands found in database.")
            
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

st.title("💊 PharmaPrice Assistant")

if medicines is None:
    st.error("Error: 'formatted_medicines_v3.csv' not found.")
else:
    if st.session_state['ocr_results']:
        st.subheader("📋 Prescription Analysis")
        st.info(f"Found {len(st.session_state['ocr_results'])} items matching your database.")
        
        for item in st.session_state['ocr_results']:
            with st.expander(f"💊 **{item}**", expanded=False):
                data = medicines[item]
                current_price = data['price']
                generic = data['generic_name']
                
                c1, c2 = st.columns([1, 2])
                c1.metric("Price", f"৳{current_price:.2f}")
                
                alternatives = df[df['generic_name'] == generic]
                cheapest_row = alternatives.loc[alternatives['price'].idxmin()]
                
                if cheapest_row['price'] < current_price:
                    savings = current_price - cheapest_row['price']
                    c2.success(f"💡 Switch to **{cheapest_row['brand_name']}** (৳{cheapest_row['price']:.2f}) to save ৳{savings:.2f}")
                else:
                    c2.info("✅ Best price available.")

        if st.button("Clear Results"):
            st.session_state['ocr_results'] = []
            st.rerun()
        
        st.divider()

    st.markdown("### 🔎 Manual Search")
    
    user_input = st.text_input(
        "Search for a medicine:", 
        placeholder="e.g., Abemaciclib or Tivizid 300",
        key="search_input"
    )

    if user_input:
        match_result = process.extractOne(user_input.lower(), medicines.keys())
        
        if match_result:
            best_match, score = match_result
            
            if score >= 60:
                data = medicines[best_match]
                current_price = data['price']
                generic = data['generic_name']

                st.divider()
                st.subheader(f"Results for: {best_match}")
                
                col1, col2 = st.columns(2)
                col1.metric("Current Price", f"৳{current_price:.2f}")
                col2.write(f"**Generic Formula:** \n{generic}")

                alternatives = df[df['generic_name'] == generic]
                
                if not alternatives.empty:
                    cheapest_row = alternatives.loc[alternatives['price'].idxmin()]
                    cheapest_name = cheapest_row['brand_name']
                    cheapest_price = cheapest_row['price']

                    if cheapest_price < current_price:
                        savings = current_price - cheapest_price
                        st.success(f"### 💡 Savings Tip")
                        st.write(f"You could save **৳{savings:.2f}** by switching brands.")
                        st.metric("Lowest Available Price", f"৳{cheapest_price:.2f}", delta=f"-৳{savings:.2f}")
                        st.info(f"**Recommended Brand:** {cheapest_name}")
                    
                    elif best_match.lower() == generic.lower():
                         st.info(f"### ℹ️ Purchase Advice")
                         st.write(f"The lowest price brand for this generic is **{cheapest_name}**.")
                         st.metric("Lowest Price", f"৳{cheapest_price:.2f}")

                    else:
                        st.balloons() 
                        st.success(f"✅ **Great Choice!** {best_match} is currently the cheapest brand.")
            else:
                st.error(f"No match found for '{user_input}'. Try typing manually.")