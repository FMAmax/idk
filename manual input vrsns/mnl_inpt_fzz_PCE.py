import pandas as pd
from thefuzz import process

try:
    df = pd.read_csv(r'F:\pybls\csv files\medicines_sample10.csv')
    medicines = df.set_index('brand_name').to_dict('index')
    print(f"--- Database Loaded: {len(medicines)} medicines found ---")
except FileNotFoundError:
    print("Error: 'medicines.csv' not found. Please create the file first.")
    exit()

while True:
    print("\n" + "="*30)
    user_input = input("Enter medicine name (or 'exit' to quit): ").strip().lower()

    if user_input in ["quit", "exit", "stop"]:
        print("Closing program. stay healthy!")
        break

    if not user_input:
        continue

    match_result = process.extractOne(user_input, medicines.keys())
    
    if match_result:
        best_match, score = match_result
        
        if score >= 70:
            if score < 100:
                confirm = input(f"Did you mean '{best_match.capitalize()}'? (y/n): ").lower()
                if confirm != 'y':
                    print("Search cancelled.")
                    continue
            
            brand_data = medicines[best_match]
            brand_price = brand_data['price']
            gen_name = brand_data['generic_name']

            print(f"\n✅ Brand: {best_match.capitalize()}")
            print(f"💰 Price: ${brand_price:.2f}")

            if gen_name and gen_name != best_match and gen_name in medicines:
                gen_price = medicines[gen_name]['price']
                savings = brand_price - gen_price
                
                print(f"💡 Generic Alternative: {gen_name.capitalize()}")
                print(f"💵 Generic Price: ${gen_price:.2f}")
                
                if savings > 0:
                    print(f"✨ Potential Savings: ${savings:.2f}")
            else:
                print("ℹ️ No cheaper generic alternative found in database.")
        
        else:
            print("❌ No close match found. Please check your spelling.")
    else:
        print("❌ Database is empty or search failed.")