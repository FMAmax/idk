import pandas as pd
from thefuzz import process


try:
    
    df = pd.read_csv(r'F:\pybls\formatted_medicines_v2.csv')
    
    df = df.drop_duplicates(subset=['brand_name'], keep='first')
    
    medicines = df.set_index('brand_name').to_dict('index')
    print(f"--- Database Loaded: {len(medicines)} items found ---")
except FileNotFoundError:
    print("Error: 'formatted_medicines_v2.csv' not found. Run your processing script first.")
    exit()

while True:
    print("\n" + "="*50)
    user_input = input("Enter Medicine & Strength (e.g., 'Tivizid 300') or 'exit': ").strip().lower()

    if user_input in ["quit", "exit"]:
        break

    if not user_input:
        continue

    match_result = process.extractOne(user_input, medicines.keys())
    
    if match_result:
        best_match, score = match_result
        
        if score >= 65:
            if score < 100:
                print(f"🔍 Closest match: {best_match}")
                confirm = input("Is this correct? (y/n): ").lower()
                if confirm != 'y': continue

            data = medicines[best_match]
            current_price = data['price']
            generic = data['generic_name']

            print(f"\n✅ PRODUCT: {best_match}")
            print(f"💰 PRICE:   ৳{current_price:.2f}")
            print(f"🧬 GENERIC: {generic}")

            alternatives = df[(df['generic_name'] == generic) & (df['brand_name'] != best_match)]
            
            if not alternatives.empty:
                cheapest_row = alternatives.loc[alternatives['price'].idxmin()]
                cheapest_name = cheapest_row['brand_name']
                cheapest_price = cheapest_row['price']

                if cheapest_price < current_price:
                    savings = current_price - cheapest_price
                    print(f"\n💡 SAVINGS TIP:")
                    print(f"   You could save ৳{savings:.2f} by choosing:")
                    print(f"   -> {cheapest_name} (৳{cheapest_price:.2f})")
                else:
                    print("\nℹ️ You are already looking at the cheapest option for this generic.")
            else:
                print("\nℹ️ No other brands found for this generic formula.")
        else:
            print("❌ Could not find a matching medicine. Try including the mg.")
    else:
        print("❌ Search failed.")