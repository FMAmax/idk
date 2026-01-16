import pandas as pd
import re

df = pd.read_csv(r'F:\pybls\csv files\medicine.csv')

def extract_price(text):
    if pd.isna(text): return 0.0
    match = re.search(r'৳\s*([\d.]+)', str(text))
    return float(match.group(1)) if match else 0.0

df['clean_price'] = df['package container'].apply(extract_price)
brands = pd.DataFrame()
brands['brand_name'] = df['brand name'].astype(str) + " " + df['strength'].astype(str)
brands['price'] = df['clean_price']
brands['generic_name'] = df['generic']

generics = df.groupby('generic')['clean_price'].min().reset_index()
generics.columns = ['brand_name', 'price']
generics['generic_name'] = generics['brand_name']

final_df = pd.concat([brands, generics], ignore_index=True)

final_df = final_df.sort_values(by=['generic_name', 'brand_name'])

final_df.to_csv('formatted_medicines_v2.csv', index=False)

print("Process Complete! Your specific brand names now include strength.")
print(final_df.head(10))