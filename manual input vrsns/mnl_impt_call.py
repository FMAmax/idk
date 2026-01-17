mednames={
    "tylenol" :9.99,
    "napa" :10.67,
    "ace" :8.42,
}
while True:
    medicine=input("Enter medicine name: ")
    if medicine.lower() in mednames:
        price=mednames[medicine.lower()]
        print(f"The price of {medicine} is ${price} ")
    else:
        print("Medicine not found")
    



    
    
    
