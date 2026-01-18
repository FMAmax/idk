import streamlit as st
import pandas as pd
from thefuzz import process
from PIL import Image
import pytesseract

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

# -------------------------------------------------------------------------
# 2. DATA LOADING
# -------------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(r'F:\pybls\csv files\formatted_medicines_v3.csv')
        df_clean = df.drop_duplicates(subset=['brand_name'], keep='first')
        return df, df_clean.set_index('brand_name').to_dict('index')
    except FileNotFoundError:
        return None, None

df, medicines = load_data()

# -------------------------------------------------------------------------
# 3. SIDEBAR: BATCH OCR UPLOADER
# -------------------------------------------------------------------------
st.sidebar.header("📷 Scan Prescription")
uploaded_file = st.sidebar.file_uploader("Upload prescription image:", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.sidebar.image(image, caption='Uploaded Image', use_container_width=True)
        
        if st.sidebar.button("🔍 Analyze Prescription"):
            st.sidebar.write("Processing lines...")
            raw_text = pytesseract.image_to_string(image)
            lines = raw_text.split('\n')
            found_items = []
            
            for line in lines:
                clean_line = line.strip()
                # Basic noise filtering
                if len(clean_line) < 4: continue
                if any(x in clean_line.lower() for x in ['date:', 'time:', 'diet:', 'doctor', 'dr.']): continue
                
                # Fuzzy Match
                match_result = process.extractOne(clean_line.lower(), medicines.keys())
                if match_result:
                    best_match, score = match_result
                    if score >= 60:
                        found_items.append(best_match)
            
            if found_items:
                st.session_state['ocr_results'] = list(set(found_items))
                st.sidebar.success(f"Found {len(found_items)} medicines!")
                st.rerun()
            else:
                st.sidebar.warning("Could not identify any known medicines.")
            
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# -------------------------------------------------------------------------
# 4. MAIN INTERFACE
# -------------------------------------------------------------------------
st.title("💊 PharmaPrice Assistant")

if medicines is None:
    st.error("Error: 'formatted_medicines_v3.csv' not found.")
else:
    # --- SECTION A: OCR BATCH RESULTS (Only shows if OCR was used) ---
    if st.session_state['ocr_results']:
        st.subheader("📋 Prescription Analysis")
        st.info(f"We identified {len(st.session_state['ocr_results'])} items from your scan.")
        
        for item in st.session_state['ocr_results']:
            with st.expander(f"💊 **{item}**", expanded=False):
                data = medicines[item]
                current_price = data['price']
                generic = data['generic_name']
                
                c1, c2 = st.columns([1, 2])
                c1.metric("Price", f"৳{current_price:.2f}")
                
                # Simple check for the list view
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

    # --- SECTION B: MANUAL SEARCH (Restored Original Logic) ---
    st.markdown("### 🔎 Manual Search")
    
    # 1. Restored Placeholder Text
    user_input = st.text_input(
        "Search for a medicine:", 
        placeholder="e.g., Abemaciclib or Tivizid 300",
        key="search_input"
    )

    if user_input:
        match_result = process.extractOne(user_input.lower(), medicines.keys())
        
        if match_result:
            best_match, score = match_result
            
            if score >= 65:
                # Retrieve Data
                data = medicines[best_match]
                current_price = data['price']
                generic = data['generic_name']

                # 2. Restored Detailed Layout
                st.divider()
                st.subheader(f"Results for: {best_match}")
                
                col1, col2 = st.columns(2)
                col1.metric("Current Price", f"৳{current_price:.2f}")
                col2.write(f"**Generic Formula:** \n{generic}")

                # 3. Restored Smart Logic
                alternatives = df[df['generic_name'] == generic]
                
                if not alternatives.empty:
                    cheapest_row = alternatives.loc[alternatives['price'].idxmin()]
                    cheapest_name = cheapest_row['brand_name']
                    cheapest_price = cheapest_row['price']

                    # Case A: Found a Cheaper Option
                    if cheapest_price < current_price:
                        savings = current_price - cheapest_price
                        st.success(f"### 💡 Savings Tip")
                        st.write(f"You could save **৳{savings:.2f}** by switching brands.")
                        st.metric("Lowest Available Price", f"৳{cheapest_price:.2f}", delta=f"-৳{savings:.2f}")
                        st.info(f"**Recommended Brand:** {cheapest_name}")
                    
                    # Case B: User searched the Generic Name directly
                    elif best_match.lower() == generic.lower():
                         st.info(f"### ℹ️ Purchase Advice")
                         st.write(f"The lowest price brand for this generic is **{cheapest_name}**.")
                         st.metric("Lowest Price", f"৳{cheapest_price:.2f}")

                    # Case C: Already Best Choice
                    else:
                        st.balloons() 
                        st.success(f"✅ **Great Choice!** {best_match} is currently the cheapest brand for this generic.")
                
            else:
                st.error(f"No match found for '{user_input}'. Try typing manually.")