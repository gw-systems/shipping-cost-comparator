import pandas as pd
import os

# Path to your database
DATA_PATH = os.path.join("app", "data", "pincode_master.csv")

if not os.path.exists(DATA_PATH):
    print("File not found!")
else:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    # Find all rows where the pincode appears more than once
    # keep=False ensures ALL copies of the duplicate are shown
    duplicates = df[df.duplicated(subset=['pincode'], keep=False)]
    
    # Sort them so they appear next to each other
    duplicates = duplicates.sort_values(by='pincode')

    if duplicates.empty:
        print("No duplicates found!")
    else:
        print(f"Found {len(duplicates)} total rows that have duplicate pincodes.")
        print("-" * 50)
        # Show first 20 rows of duplicates
        print(duplicates[['pincode', 'office', 'district', 'state']].head(20))
        
        # Save them to a CSV so you can inspect them in Excel properly
        duplicates.to_csv("duplicate_pincodes_report.csv", index=False)
        print("-" * 50)
        print("Full report saved to: duplicate_pincodes_report.csv")