import pandas as pd
import random

# Mappings
# Insurance Types: 1=Life, 2=Motor, 3=Health, 4=Corporate
# Budget: 1=Economy, 2=Standard, 3=Premium

def get_policy(ins_type, age, income, budget, cover):
    # Logic to assign realistic policies based on profile
    
    # --- LIFE INSURANCE (1) ---
    if ins_type == 1:
        if budget == 3 or income > 15:
            return "HDFC Life Click 2 Protect (Term)"
        elif age > 50:
            return "LIC Jeevan Umang (Whole Life)"
        elif budget == 1:
            return "SBI Life Saral (Standard)"
        else:
            return "Max Life Smart Term"

    # --- MOTOR INSURANCE (2) ---
    elif ins_type == 2:
        if budget == 3: # Premium
            return "ICICI Lombard Zero Depreciation"
        elif budget == 1: # Economy
            return "Digit Third Party Only"
        else:
            return "HDFC Ergo Comprehensive"

    # --- HEALTH INSURANCE (3) ---
    elif ins_type == 3:
        if age > 55:
            return "Care Senior Citizen Plan"
        elif budget == 3:
            return "Star Health Premier (50L Cover)"
        elif budget == 1:
            return "Niva Bupa ReAssure (Basic)"
        else:
            return "HDFC Ergo Optima Restore"

    # --- CORPORATE INSURANCE (4) ---
    elif ins_type == 4:
        if budget == 3:
            return "Plum HQ Comprehensive Group Health"
        elif budget == 1:
            return "New India Workmen Compensation"
        else:
            return "ICICI Lombard SME Package"
            
    return "Standard Policy"

# Generate 500 rows
data = []
for _ in range(500):
    ins_type = random.choice([1, 2, 3, 4])
    age = random.randint(21, 65)
    income = random.randint(3, 30) # Lakhs
    budget = random.choice([1, 2, 3])
    
    # Cover depends on type slightly
    if ins_type == 1: cover = random.choice([50, 100, 200]) # Life
    elif ins_type == 3: cover = random.choice([5, 10, 20])  # Health
    else: cover = 0 # Not main factor for Motor/Corp prediction in this simplified model
    
    policy = get_policy(ins_type, age, income, budget, cover)
    
    data.append([ins_type, age, income, budget, cover, policy])

# Save
df = pd.DataFrame(data, columns=["insurance_type", "age", "income", "budget", "cover", "policy"])
df.to_csv("insurance_data.csv", index=False)
print("Generated insurance_data.csv with 500 rows.")
