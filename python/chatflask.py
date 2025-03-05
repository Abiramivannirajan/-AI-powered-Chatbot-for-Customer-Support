
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import process, fuzz
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load NLP Model
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

# File Paths
DATASET_PATH = "chatbot_dataset.json"
EMBEDDINGS_PATH = "embeddings.npy"

def load_data():
    """Load chatbot dataset and embeddings."""
    if not os.path.exists(DATASET_PATH) or not os.path.exists(EMBEDDINGS_PATH):
        print("Error: Dataset or embeddings file not found!")
        return None, None

    try:
        with open(DATASET_PATH, "r") as file:
            dataset = json.load(file)
        embeddings = np.load(EMBEDDINGS_PATH)
        print("Chatbot data loaded successfully!")
        return dataset, embeddings
    except Exception as e:
        print(f"Error loading files: {e}")
        return None, None

# Load chatbot data at startup
qa_data, embeddings = load_data()

def find_best_match(user_input, questions):
    """Find the best matching question using fuzzy matching."""
    best_match, score, index = process.extractOne(user_input, questions, scorer=fuzz.partial_ratio)
    return index if score > 65 else -1  # Adjust threshold for better results

@app.route('/chat', methods=['POST'])
def chatbot():
    """Handle chatbot requests."""
    global qa_data, embeddings  

    if qa_data is None or embeddings is None:
        return jsonify({"response": "Chatbot is not trained yet. Please train first."}), 500

    data = request.get_json()
    user_message = data.get("user_input", "").strip().lower()

    if not user_message:
        return jsonify({"response": "Please enter a valid question."}), 400

    # Find best matching question
    questions = [item["question"] for item in qa_data]
    best_match_index = find_best_match(user_message, questions)

    if best_match_index == -1:
        return jsonify({"response": "Sorry, I don't understand that question."}), 200

    return jsonify({"response": qa_data[best_match_index]["answer"]}), 200

@app.route('/refresh', methods=['POST'])
def refresh_chatbot():
    """Manually reload dataset and embeddings."""
    global qa_data, embeddings
    qa_data, embeddings = load_data()

    if qa_data is None or embeddings is None:
        return jsonify({"message": "Failed to reload chatbot data. Check files!"}), 500

    return jsonify({"message": "Chatbot dataset reloaded successfully!"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
