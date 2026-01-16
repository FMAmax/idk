import pandas as pd
from thefuzz import process


df = pd.read_csv('medicines.csv')

medicines = dict(zip(df['brand_name'], df['price']))

while True:
    user_input = input("\nEnter medicine name (or type 'exit'): ").strip().lower()
    
    if user_input in ["quit", "exit"]:
        break

    match_result = process.extractOne(user_input, medicines.keys())
    
    if match_result:
        best_match, score = match_result
        if score >= 75:
            price = medicines[best_match]
            print(f"Match found: {best_match.capitalize()} - ${price:.2f}")
        else:
            print("Medicine not found. Try checking the spelling.")