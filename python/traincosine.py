import pandas as pd
import numpy as np
import os
import ssl
import couchdb
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Connect to CouchDB
couch = couchdb.Server('https://192.168.57.185:5984/dpg_chatbot')  # Make sure to use HTTP if no SSL is required
db_name = 'dpg_chatbot'

# Create the database if it doesn't exist
if db_name not in couch:
    db = couch.create(db_name)
    print(f"Database '{db_name}' created.")
else:
    db = couch[db_name]
    print(f"Connected to database: {db_name}")

# Load dataset
df = pd.read_csv('qa_dataset.csv')

# Ensure dataset integrity
if df.isnull().values.any():
    print("Error: Missing values found in dataset. Please clean the CSV file.")
    exit()

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
embeddings = model.encode(df['question'].tolist())

# Store embeddings and questions in CouchDB
for i, question in enumerate(df['question']):
    # Prepare the document to store
    doc = {
        'question': question,
        'embedding': embeddings[i].tolist()  # Convert numpy array to list for storage
    }
    
    # Store the document in CouchDB
    db.save(doc)

# Confirm dataset size
print(f"Total questions in dataset: {len(df)}")
print(f"Shape of embeddings: {embeddings.shape}")
print("Embeddings saved to CouchDB successfully!")

# Function to handle chatbot responses
def get_response(query):
    # Generate the embedding for the query
    query_embedding = model.encode([query])[0]

    # Retrieve all embeddings from the database
    all_docs = db.view('_all_docs', include_docs=True)
    
    # Calculate cosine similarity for each document in the database
    similarities = []
    for row in all_docs:
        doc = row['doc']
        stored_embedding = np.array(doc['embedding'])
        
        # Compute cosine similarity between query and stored embedding
        similarity = cosine_similarity([query_embedding], [stored_embedding])
        similarities.append((doc['question'], similarity[0][0]))
    
    # Sort based on similarity score
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return the most similar question and its answer
    most_similar = similarities[0]
    print(f"Bot: {most_similar[0]} (Similarity: {most_similar[1]:.3f})")

# Test chatbot response
query = "What is the process for onboarding new users?"
get_response(query)
