import os
import numpy as np
import pandas as pd
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Paths to dataset and embeddings
qa_dataset_path = 'qa_dataset.csv'
embedding_path = 'qa_dataset_model.npy'

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to load dataset and embeddings
def load_embeddings():
    global df, embeddings

    # Reload dataset
    df = pd.read_csv(qa_dataset_path)

    # Ensure dataset is clean
    df = df.dropna(subset=['question', 'answer'])
    df['question'] = df['question'].str.strip()
    df['answer'] = df['answer'].str.strip()

    # Reload embeddings
    embeddings = np.load(embedding_path)

    print(f" Embeddings reloaded! Total questions: {len(df)}")

# Load dataset and embeddings when Flask starts
load_embeddings()

# Function to get chatbot response
def get_chatbot_response(user_input):
    # Generate embedding for user input
    user_input_embedding = model.encode([user_input])

    # Ensure embeddings exist
    if len(embeddings) == 0:
        return "Sorry, I don't have enough data to answer that."

    # Calculate cosine similarity
    similarities = cosine_similarity(user_input_embedding, embeddings)

    # Get best match index
    best_match_index = np.argmax(similarities)

    # Set similarity threshold
    threshold = 0.5  
    if similarities[0][best_match_index] < threshold:
        return "Sorry, I couldn't understand your question. Please rephrase it."

    # Return best-matching answer
    return df.iloc[best_match_index]['answer']

# Chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('user_input', '')
    bot_response = get_chatbot_response(user_input)
    return jsonify({'bot_response': bot_response})

# Update dataset endpoint (for dynamic learning)
@app.route('/update', methods=['POST'])
def update_dataset():
    new_question = request.json.get('question', '').strip()
    new_answer = request.json.get('answer', '').strip()

    if new_question and new_answer:
        global df, embeddings

        # Append new data
        new_entry = pd.DataFrame([[new_question, new_answer]], columns=['question', 'answer'])
        df = pd.concat([df, new_entry], ignore_index=True)

        # Save updated dataset
        df.to_csv(qa_dataset_path, index=False)

        #  Retrain embeddings for the new dataset
        embeddings = model.encode(df['question'].tolist())
        np.save(embedding_path, embeddings)

        #  Reload embeddings into memory
        load_embeddings()

        return jsonify({'message': 'Dataset updated and embeddings reloaded!'})

    return jsonify({'error': 'Invalid input'}), 400

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
    
