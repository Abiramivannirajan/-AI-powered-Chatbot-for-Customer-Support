from flask import Flask, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS
import os
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Load dataset
file_path = 'skill_assessment.csv'

if not os.path.exists(file_path):
    raise FileNotFoundError(f"File '{file_path}' not found. Please check the file path.")

df = pd.read_csv(file_path)

# Ensure 'Score' column exists and is numeric
if 'Score' not in df.columns:
    raise KeyError("Dataset is missing the 'Score' column.")

df['Score'] = pd.to_numeric(df['Score'], errors='coerce')  # Convert to numeric
df = df.dropna(subset=['Score'])  # Drop rows with NaN scores

# Preprocess dataset (Convert all answers to lowercase and strip spaces)
df.iloc[:, :-1] = df.iloc[:, :-1].map(lambda x: str(x).strip().lower())

# Train TF-IDF Model
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df.iloc[:, :-1].astype(str).apply(lambda row: ' '.join(row), axis=1))

@app.route('/predict', methods=['POST'])
def predict_skill():
    try:
        # Get JSON data
        data = request.get_json()
        print(" Received Request:", data)

        if not data or 'answers' not in data:
            return jsonify({'error': 'Invalid request. Expected JSON with key "answers".'}), 400

        user_inputs = data['answers']
        print("Processed Inputs:", user_inputs)

        # Validate input format
        if not isinstance(user_inputs, list) or len(user_inputs) != 5:
            return jsonify({'error': 'Invalid input. Provide exactly 5 Yes/No answers.'}), 400

        # Normalize inputs
        user_inputs = [ans.lower().strip() for ans in user_inputs]
        print(" Normalized Inputs:", user_inputs)

        if not all(ans in ['yes', 'no'] for ans in user_inputs):
            return jsonify({'error': "Invalid answers. Allowed values: 'yes' or 'no'."}), 400

        # Convert user inputs into TF-IDF vector
        user_vector = vectorizer.transform([' '.join(user_inputs)])
        print(" User Vector Shape:", user_vector.shape)

        # Calculate similarity
        similarities = cosine_similarity(user_vector, X).flatten()
        print(" Similarity Scores:", similarities)

        # Get the best match index
        best_match_index = similarities.argmax()
        confidence = similarities[best_match_index]
        print(" Best Match Index:", best_match_index, "Confidence:", confidence)

        # Ensure index is valid
        if best_match_index >= len(df):
            print(" Best match index out of range")
            return jsonify({'error': 'No matching skill found.'}), 400

        # Get predicted score
        score = df.iloc[best_match_index]['Score']
        print(" Predicted Score (Raw):", score)

        # Convert score to numeric
        score = pd.to_numeric(score, errors='coerce')
        print("Final Score:", score)

        if pd.isna(score):
            return jsonify({'error': 'Invalid score found in dataset.'}), 400

        return jsonify({
            'score': float(score),
            'confidence': round(float(confidence), 2)
        })

    except Exception as e:
        print(" Error:", traceback.format_exc())
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
