from thefuzz import process  

medicines = {
    "tylenol": 5.99,
    "advil": 7.50,
    "aspirin": 4.25
}

while True:
    user_input = input("\nEnter medicine name (or type 'exit' to quit): ").strip()
    
    if user_input.lower() in ["quit", "exit"]:
        print("Exiting the program. Goodbye!")
        break

    match_result = process.extractOne(user_input.lower(), medicines.keys())
    
    if match_result:
        best_match, score = match_result
        
        if score == 100:
            price = medicines[best_match]
            print(f"The price of {best_match.capitalize()} is ${price}")
        elif score >= 75:
            confirm = input(f"Did you mean '{best_match.capitalize()}'? (yes/no): ").lower()
            if confirm == 'yes':
                price = medicines[best_match]
                print(f"The price of {best_match.capitalize()} is ${price}")
            else:
                print("Medicine not found. Please try again.")
        else:
            print("Medicine not found. Please check the spelling.")
    else:
        print("Medicine not found.")