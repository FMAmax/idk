import streamlit as st
import pandas as pd
from thefuzz import process

st.set_page_config(page_title="PharmaPrice Assistant", page_icon="💊")
st.title("💊 PharmaPrice Assistant")
st.markdown("Find the best prices for your medications and discover cheaper alternatives.")

@st.cache_data
def load_data():
    df = pd.read_csv(r'F:\pybls\formatted_medicines_v3.csv')
    df_clean = df.drop_duplicates(subset=['brand_name'], keep='first')
    return df, df_clean.set_index('brand_name').to_dict('index')

df, medicines = load_data()

user_input = st.text_input("Search for a medicine (include strength for better results):", 
                          placeholder="e.g., Abemaciclib or Tivizid 300")

if user_input:
    match_result = process.extractOne(user_input.lower(), medicines.keys())
    
    if match_result:
        best_match, score = match_result
        
        if score >= 65:
            data = medicines[best_match]
            current_price = data['price']
            generic = data['generic_name']

            st.divider()
            st.subheader(f"Results for: {best_match.capitalize()}")
            
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
                    st.write(f"You could save **৳{savings:.2f}** by switching to a different brand.")
                    st.metric("Lowest Available Price", f"৳{cheapest_price:.2f}", delta=f"-৳{savings:.2f}")
                    st.info(f"**Recommended Brand:** {cheapest_name}")
                
                elif best_match.lower() == generic.lower():
                     st.info(f"### ℹ️ Purchase Advice")
                     st.write(f"The lowest price brand for this generic is **{cheapest_name}**.")
                     st.metric("Lowest Price", f"৳{cheapest_price:.2f}")

                else:
                    st.balloons() 
                    st.success(f"✅ **Great Choice!** {best_match} is currently the cheapest brand for this generic.")
            
        else:
            st.error("Medicine not found. Try adjusting your spelling or adding the strength (mg).")