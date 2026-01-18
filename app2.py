import streamlit as st
import pandas as pd
from thefuzz import process
from PIL import Image
import pytesseract


st.set_page_config(page_title="PharmaPrice Assistant", page_icon="💊")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


if 'search_term' not in st.session_state:
    st.session_state.search_term = ''

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(r'F:\pybls\csv files\formatted_medicines_v3.csv')
        df_clean = df.drop_duplicates(subset=['brand_name'], keep='first')
        return df, df_clean.set_index('brand_name').to_dict('index')
    except FileNotFoundError:
        return None, None

df, medicines = load_data()

st.sidebar.header("📷 Scan Prescription")
uploaded_file = st.sidebar.file_uploader("Upload a photo of the medicine text:", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        
        st.sidebar.image(image, caption='Uploaded Image', use_container_width=True)
        st.sidebar.write("Reading text...")
        extracted_text = pytesseract.image_to_string(image).strip()
        
        
        clean_text = " ".join(extracted_text.split())
        
        if clean_text:
            st.sidebar.success("Text found!")
            st.session_state['search_input'] = clean_text
            st.rerun()
        else:
            st.sidebar.warning("Could not read any clear text.")
            
    except Exception as e:
        st.sidebar.error(f"Error processing image: {e}")

st.title("💊 PharmaPrice Assistant")
st.markdown("Find the best prices for your medications.")

if medicines is None:
    st.error("Error: 'formatted_medicines_v3.csv' not found. Please run your processing script first.")
else:
   
    user_input = st.text_input(
        "Search for a medicine:", 
        value=st.session_state.search_term,
        placeholder="e.g., Abemaciclib or Tivizid 300",
        key="search_input"
    )

    if user_input:
        match_result = process.extractOne(user_input.lower(), medicines.keys())
        
        if match_result:
            best_match, score = match_result
            
            # Threshold Check
            if score >= 60:
                # Retrieve Data
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

                    # Case A: Found a Cheaper Option
                    if cheapest_price < current_price:
                        savings = current_price - cheapest_price
                        st.success(f"### 💡 Savings Tip")
                        st.write(f"You could save **৳{savings:.2f}** by switching to a different brand.")
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
                st.error(f"No match found for '{user_input}'. Try typing the name manually.")
                if uploaded_file:
                    st.warning("OCR Tip: Make sure the photo is clear and the text is horizontal.")