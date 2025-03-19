import requests
import json
import ssl  
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import urllib3
from textblob import TextBlob 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# SSL Handling for HTTPS requests
ssl._create_default_https_context = ssl._create_unverified_context

COUCHDB_URL = "https://192.168.57.185:5984"
DB_NAME = "dpg_chatbot"
DESIGN_DOC = "view"  # Ensure this matches your design document name
VIEW_NAME = "jobdetails_by_id"

VIEW_URL = f"{COUCHDB_URL}/{DB_NAME}/_design/{DESIGN_DOC}/_view/{VIEW_NAME}?include_docs=true"

# Gemini API details
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = "AIzaSyBLxzeAh498flmqTsgZ8_R3QmXnfpqST9s"
GEMINI_HEADERS = {"Content-Type": "application/json"}

# Fetch job data from CouchDB
def fetch_job_data():
    try:
        response = requests.get(VIEW_URL, auth=("d_couchdb", "Welcome#2"), verify=False)
        response.raise_for_status()
        job_data = response.json()
        
        if "rows" not in job_data or not isinstance(job_data["rows"], list):
            print("Invalid response format from CouchDB")
            return []
        
        job_list = []
        for row in job_data["rows"]:
            doc = row.get("doc", {})
            job_details = doc.get("data", {})
            if isinstance(job_details, dict) and "companyName" in job_details:
                job_list.append(job_details)
        return job_list
    except requests.exceptions.RequestException as e:
        print("Error fetching job data:", str(e))
        return []

# Create FAISS index for job listings
def create_faiss_index(jobs):
    job_descriptions = [
        f"{job.get('jobRole', 'Unknown Job')} at {job.get('companyName', 'Unknown Company')} in {job.get('location', 'Unknown Location')}"
        for job in jobs
    ]
    embeddings = embedding_model.encode(job_descriptions)
    
    dimension = embeddings.shape[1]  # Size of the vector
    index = faiss.IndexFlatL2(dimension)  # Index for nearest neighbor search & Euclidean distance metric
    index.add(np.array(embeddings, dtype=np.float32))  # Add embeddings to the index
    
    return index, job_descriptions, jobs

# Perform similarity search
def search_jobs(query, index, job_descriptions, jobs, top_k=5):
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding, dtype=np.float32), top_k)
    return [jobs[i] for i in indices[0] if i < len(jobs)]

# Process query with Gemini AI
def process_with_gemini(query, index, job_descriptions, jobs):
    corrected_query = str(TextBlob(query).correct())  # Corrected this line
    relevant_jobs = search_jobs(corrected_query, index, job_descriptions, jobs)
    
    if not relevant_jobs:
        return "I'm sorry, I couldn't find job listings related to your query."
    
    job_json = json.dumps(relevant_jobs, indent=2)
    prompt = f"""
    You are a job search assistant. You have access to the following job data:
    
    {job_json}
    
    Answer the following question based on the data available:
    "{corrected_query}"
    
    If the answer isn't found in the job data, respond with "I'm sorry, I couldn't find that information."
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],  # Convert Python dictionary to JSON
        "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": 1}],
    }

    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        headers=GEMINI_HEADERS,
        data=json.dumps(payload),
    )
    
    if response.status_code == 200:
        gemini_response = response.json()
        try:
            return gemini_response["candidates"][0]["content"]["parts"][0]["text"].strip()
        except KeyError:
            return "Unexpected response format from Gemini."
    else:
        return "Error processing request with Gemini."

# Main chatbot function
def chatbot():
    print("\nWelcome to the AI-Powered Job Chatbot with FAISS & Gemini!")
    print("Type 'exit' to quit.\n")
    
    job_data = fetch_job_data()
    if not job_data:
        print("No job data available. Please check your database connection.")
        return
    
    index, job_descriptions, jobs = create_faiss_index(job_data)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        response = process_with_gemini(user_input, index, job_descriptions, jobs)
        print(f"\nBot: {response}\n")

# Run the chatbot
if __name__ == "__main__":
    chatbot()