
from flask import Flask, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS  # To allow Angular frontend requests
import os  # For file checking

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load the dataset
file_path = 'Book1.csv'  # Ensure the CSV file is in the same directory

if not os.path.exists(file_path):
    raise FileNotFoundError(f"File '{file_path}' not found. Please check the file path.")

df = pd.read_csv(file_path)

# Ensure correct column names
expected_columns = [f'Q{i}' for i in range(1, 21)] + ['Department']
if list(df.columns) != expected_columns:
    df.columns = expected_columns  # Rename if needed

print("Dataset Loaded Successfully")

# Convert all Yes/No answers to lowercase for consistency
df.iloc[:, :-1] = df.iloc[:, :-1].applymap(lambda x: str(x).strip().lower())

# Train the TF-IDF model
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df.iloc[:, :-1].astype(str).apply(lambda row: ' '.join(row), axis=1))

@app.route('/predict', methods=['POST'])
def predict_department():
    """ Predict department based on user inputs. """
    try:
        data = request.json
        user_inputs = data.get('answers')

        if not user_inputs or len(user_inputs) != 20:
            return jsonify({'error': 'Invalid input. Please provide exactly 20 Yes/No answers'}), 400

        # Convert user input to lowercase for consistency
        user_inputs = [str(ans).strip().lower() for ans in user_inputs]
        
        # Transform user inputs to match dataset
        user_vector = vectorizer.transform([' '.join(user_inputs)])
        similarities = cosine_similarity(user_vector, X).flatten()
        best_match_index = similarities.argmax()
        confidence = similarities[best_match_index]

        if confidence > 0:
            department = df.iloc[best_match_index]['Department']
            return jsonify({'department': department, 'confidence': round(float(confidence), 2)})
        else:
            return jsonify({'department': 'No matching department found', 'confidence': 0})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


# {
#   "answers": ["yes", "no", "yes", "no", "yes", "yes", "no", "no", "yes", "no", 
#               "yes", "yes", "no", "yes", "no", "yes", "no", "yes", "no", "yes"]
# }

#  Output (Prediction)

# {
#   "department": "Computer Science",
#   "confidence": 0.89
# }