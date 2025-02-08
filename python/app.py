import pandas as pd

def load_csv(file_path):
    """ Load CSV file and ensure column names are correct. """
    df = pd.read_csv(file_path)
    
    # Rename columns if needed (Ensure the headers are correct)
    expected_columns = [f'Q{i}' for i in range(1, 21)] + ['Department']
    
    if list(df.columns) != expected_columns:
        df.columns = expected_columns  # Fix column names if needed
    
    print("\nCSV Loaded:")

    return df

def get_user_input():
    """ Collect 20 Yes/No inputs from the user. """
    user_inputs = []
    print("\nEnter 20 Yes/No inputs:")
    
    for i in range(1, 21):
        while True:
            answer = input(f"Q{i}: ").strip().lower()  # Convert to lowercase for consistency
            if answer in ['yes', 'no']:
                user_inputs.append(answer.capitalize())  # Store as 'Yes' or 'No' (to match CSV)
                break
            else:
                print("Invalid input! Please enter 'Yes' or 'No'.")

    print("\nUser inputs captured:", user_inputs)
    return user_inputs

def predict_department(df, user_inputs):
    """ Compare user inputs with CSV rows and return matching department. """
    for index, row in df.iterrows():
        row_values = row[:-1].tolist()  # Exclude the last column (Department)
        
        if row_values == user_inputs:
            return row['Department']
    
    return "No matching department found"

# Main Execution
file_path = 'Book1.csv'  # Ensure your CSV file is named 'Book1.csv' and is in the same directory
df = load_csv(file_path)
user_inputs = get_user_input()
predicted_department = predict_department(df, user_inputs)

print("\nPredicted Department:", predicted_department)