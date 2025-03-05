
from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

# Load the model and dataset
qa_dataset_path = 'qa_dataset.csv'
embedding_path = 'embeddings.npy'
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load dataset and embeddings
def load_embeddings():
    global df, embeddings
    df = pd.read_csv(qa_dataset_path)
    df = df.dropna(subset=['question', 'answer'])
    df['question'] = df['question'].str.strip()
    df['answer'] = df['answer'].str.strip()
    embeddings = np.load(embedding_path)

load_embeddings()

# Get chatbot response
def get_chatbot_response(user_input):
    user_input_embedding = model.encode([user_input])
    if len(embeddings) == 0:
        return "Sorry, I don't have enough data to answer that."
    similarities = cosine_similarity(user_input_embedding, embeddings)
    best_match_index = np.argmax(similarities)
    if similarities[0][best_match_index] < 0.5:
        return "Sorry, I couldn't understand your question. Please rephrase it."
    return df.iloc[best_match_index]['answer']

# Speech recognition function
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now.")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None

# Voice chat API endpoint
@app.route('/voice_chat', methods=['GET'])
def voice_chat_api():
    user_input = recognize_speech()
    if user_input:
        bot_response = get_chatbot_response(user_input)
        return jsonify({'bot_response': bot_response, 'user_input': user_input})
    return jsonify({'error': 'Speech not recognized'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
