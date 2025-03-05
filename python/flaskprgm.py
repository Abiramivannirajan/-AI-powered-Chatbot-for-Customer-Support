
import os
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Paths to dataset and embeddings
QA_DATASET_PATH = 'qa_dataset.csv'
EMBEDDING_PATH = 'embeddings.npy'

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_embeddings():
    """Load dataset and embeddings into memory."""
    global df, embeddings
    try:
        # Load dataset
        if os.path.exists(QA_DATASET_PATH):
            df = pd.read_csv(QA_DATASET_PATH)
            df = df.dropna(subset=['question', 'answer']).applymap(str.strip)
        else:
            df = pd.DataFrame(columns=['question', 'answer'])

        # Load embeddings
        if os.path.exists(EMBEDDING_PATH):
            embeddings = np.load(EMBEDDING_PATH)
        else:
            embeddings = np.array([])

        print(f"✅ Data loaded! Total questions: {len(df)}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        df = pd.DataFrame(columns=['question', 'answer'])
        embeddings = np.array([])

# Load data on startup
load_embeddings()

def get_chatbot_response(user_input):
    """Generate a chatbot response based on user input."""
    if df.empty or embeddings.size == 0:
        return "Sorry, I don't have enough data to answer that."
    
    user_input_embedding = model.encode([user_input])
    similarities = cosine_similarity(user_input_embedding, embeddings)
    best_match_index = np.argmax(similarities)
    
    if similarities[0][best_match_index] < 0.5:
        return "Sorry, I couldn't understand your question. Please rephrase it."
    
    return df.iloc[best_match_index]['answer']

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint to get bot responses"""
    user_input = request.json.get('user_input', '').strip()
    
    if not user_input:
        return jsonify({'error': 'User input is required'}), 400
    
    bot_response = get_chatbot_response(user_input)
    return jsonify({'bot_response': bot_response})

@app.route('/update', methods=['POST'])
def update_dataset():
    """Update dataset with new question-answer pairs and retrain embeddings."""
    new_question = request.json.get('question', '').strip()
    new_answer = request.json.get('answer', '').strip()
    
    if not new_question or not new_answer:
        return jsonify({'error': 'Both question and answer are required'}), 400

    global df, embeddings

    # Append new data
    new_data = pd.DataFrame([[new_question, new_answer]], columns=['question', 'answer'])
    df = pd.concat([df, new_data], ignore_index=True)
    
    # Save updated dataset
    df.to_csv(QA_DATASET_PATH, index=False)
    
    # Update embeddings
    embeddings = model.encode(df['question'].tolist())
    np.save(EMBEDDING_PATH, embeddings)
    
    # Reload everything
    load_embeddings()

    return jsonify({'message': 'Dataset updated and embeddings reloaded!'})

if __name__ == '__main__':
    print("🚀 Starting Flask Chatbot Server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
