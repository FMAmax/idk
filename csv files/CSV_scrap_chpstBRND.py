import pandas as pd
import re

# 1. Load the data
df = pd.read_csv(r'F:\pybls\csv files\medicine.csv')

# 2. Function to clean the price
def extract_price(text):
    if pd.isna(text): return 0.0
    match = re.search(r'৳\s*([\d.]+)', str(text))
    return float(match.group(1)) if match else 0.0

df['clean_price'] = df['package container'].apply(extract_price)

# 3. Create the Main List (Brand + Strength)
brands = pd.DataFrame()
brands['brand_name'] = df['brand name'].astype(str) + " " + df['strength'].astype(str)
brands['price'] = df['clean_price']
brands['generic_name'] = df['generic']
brands['cheapest_brand_ref'] = None  # Regular brands don't need this

# 4. Create 'Generic Search' Rows (The Logic Change)
# We want to find the row with the lowest price for every generic.
# Instead of groupby().min(), we SORT by price and pick the first one.
cheapest_rows = brands.sort_values('price').drop_duplicates('generic_name').copy()

# Now we transform these rows so they can be searched by their Generic Name
cheapest_rows['cheapest_brand_ref'] = cheapest_rows['brand_name'] # Save the real brand name (e.g. "Abeclib 200 mg")
cheapest_rows['brand_name'] = cheapest_rows['generic_name']       # Set lookup key to Generic Name (e.g. "Abemaciclib")

# 5. Combine everything
final_df = pd.concat([brands, cheapest_rows], ignore_index=True)

# Remove duplicates in case a brand name is exactly the same as a generic name
final_df = final_df.drop_duplicates(subset=['brand_name'], keep='last')

# Sort for neatness
final_df = final_df.sort_values(by=['generic_name', 'brand_name'])

# 6. Save
final_df.to_csv('formatted_medicines_v3.csv', index=False)

print("Process Complete. Generic search rows now point to the cheapest brand.")
print(final_df[['brand_name', 'price', 'cheapest_brand_ref']].head(10))