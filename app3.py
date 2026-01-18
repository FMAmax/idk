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

# Initialize the search box state if it doesn't exist
if 'search_input' not in st.session_state:
    st.session_state['search_input'] = ''

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
# 3. SIDEBAR: OCR UPLOADER
# -------------------------------------------------------------------------
st.sidebar.header("📷 Scan Prescription")
uploaded_file = st.sidebar.file_uploader("Upload a photo of the medicine text:", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        
        # FIX: 'use_container_width' removes the yellow warning
        st.sidebar.image(image, caption='Uploaded Image', use_container_width=True)
        
        st.sidebar.write("Reading text...")
        extracted_text = pytesseract.image_to_string(image).strip()
        clean_text = " ".join(extracted_text.split())
        
        if clean_text:
            st.sidebar.success(f"Text found: {clean_text}")
            
            # CRITICAL FIX: Check if we need to update to avoid loops
            if st.session_state['search_input'] != clean_text:
                st.session_state['search_input'] = clean_text
                st.rerun() # Forces the search box to refresh immediately
        else:
            st.sidebar.warning("Could not read any clear text.")
            
    except Exception as e:
        st.sidebar.error(f"Error processing image: {e}")

# -------------------------------------------------------------------------
# 4. MAIN INTERFACE
# -------------------------------------------------------------------------
st.title("💊 PharmaPrice Assistant")
st.markdown("Find the best prices for your medications.")

if medicines is None:
    st.error("Error: 'formatted_medicines_v3.csv' not found.")
else:
    # SEARCH BAR
    # We remove 'value=' and rely purely on 'key' to sync with the sidebar
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
                        st.success(f"✅ **Great Choice!** {best_match} is the cheapest brand.")
                
            else:
                st.error(f"No match found for '{user_input}'. Try typing manually.")