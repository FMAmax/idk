import streamlit as st
import pandas as pd
from thefuzz import process
from PIL import Image
import pytesseract

# -------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="PharmaPrice Assistant", page_icon="💊")
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize Session State
if 'search_input' not in st.session_state:
    st.session_state['search_input'] = ''
if 'ocr_results' not in st.session_state:
    st.session_state['ocr_results'] = []  # Stores list of found medicines

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
            
            # 1. Extract raw text
            raw_text = pytesseract.image_to_string(image)
            
            # 2. Split into lines
            lines = raw_text.split('\n')
            
            found_items = []
            
            # 3. Loop through every line
            for line in lines:
                clean_line = line.strip()
                
                # Filter out noise (short lines, dates, doctors names)
                if len(clean_line) < 4: continue
                if any(x in clean_line.lower() for x in ['date:', 'time:', 'diet:', 'doctor', 'dr.']): continue
                
                # Fuzzy Match this specific line
                match_result = process.extractOne(clean_line.lower(), medicines.keys())
                
                if match_result:
                    best_match, score = match_result
                    
                    # We use a threshold of 60 to catch medicines even with OCR typos
                    if score >= 60:
                        found_items.append(best_match)
            
            # 4. Save results to session state
            if found_items:
                # Remove duplicates in the list
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
    st.error("Database not found.")
else:
    # --- MODE A: PRESCRIPTION RESULTS (If OCR found items) ---
    if st.session_state['ocr_results']:
        st.subheader("📋 Prescription Analysis")
        st.info(f"We identified {len(st.session_state['ocr_results'])} items from your image.")
        
        # Create a clearer layout for list items
        for item in st.session_state['ocr_results']:
            with st.expander(f"💊 **{item}**", expanded=True):
                # Retrieve Data
                data = medicines[item]
                current_price = data['price']
                generic = data['generic_name']
                
                c1, c2, c3 = st.columns([1, 2, 2])
                c1.metric("Price", f"৳{current_price:.2f}")
                c2.write(f"**Generic:** {generic}")
                
                # Smart Suggestions Logic
                alternatives = df[df['generic_name'] == generic]
                cheapest_row = alternatives.loc[alternatives['price'].idxmin()]
                cheapest_price = cheapest_row['price']
                
                if cheapest_price < current_price:
                    savings = current_price - cheapest_price
                    c3.success(f"Savings Tip: Switch to **{cheapest_row['brand_name']}** to save ৳{savings:.2f}")
                else:
                    c3.success("✅ Best price.")

        if st.button("Clear Results"):
            st.session_state['ocr_results'] = []
            st.rerun()
            
        st.divider() # Line to separate manual search

    # --- MODE B: MANUAL SEARCH ---
    st.markdown("### 🔎 Manual Search")
    user_input = st.text_input("Type a medicine name:", key="search_input")

    if user_input:
        # (This is your existing manual search logic)
        match_result = process.extractOne(user_input.lower(), medicines.keys())
        if match_result and match_result[1] >= 60:
            best_match = match_result[0]
            current_price = data['price']
            data = medicines[best_match]
        #     st.success(f"Found: {best_match} (৳{data['price']:.2f})")
        #     # You can copy your full logic here if you want the manual search strictly separate
        # else:
        #     st.warning("No match found.")
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
                    st.success(f"✅ **Great Choice!** {best_match} is the cheapest brand.")
                
        else:
            st.error(f"No match found for '{user_input}'. Try typing manually.")