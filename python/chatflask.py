from flask import Flask, request, jsonify, flash
from flask_cors import CORS
import requests
import json
import ssl
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import urllib3
from textblob import TextBlob 

# Disable warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# SSL Handling for HTTPS requests
ssl._create_default_https_context = ssl._create_unverified_context

# CouchDB Configurations
COUCHDB_URL = "https://192.168.57.185:5984"
DB_NAME = "dpg_chatbot"
DESIGN_DOC = "view"  # Ensure this matches your design document name
VIEW_NAME = "jobdetails_by_id"

VIEW_URL = f"{COUCHDB_URL}/{DB_NAME}/_design/{DESIGN_DOC}/_view/{VIEW_NAME}?include_docs=true"

# Gemini API Details
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = "AIzaSyBLxzeAh498flmqTsgZ8_R3QmXnfpqST9s"
GEMINI_HEADERS = {"Content-Type": "application/json"}

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = "supersecretkey"  # Required for flash messages

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

        print(" Job data successfully fetched!")
        return job_list
    except requests.exceptions.RequestException as e:
        print(" Error fetching job data:", str(e))
        return []

# Create FAISS index for job listings
def create_faiss_index(jobs):
    job_descriptions = [
        f"{job.get('jobRole', 'Unknown Job')} at {job.get('companyName', 'Unknown Company')} in {job.get('location', 'Unknown Location')}"
        for job in jobs
    ]
    embeddings = embedding_model.encode(job_descriptions)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))

    return index, job_descriptions, jobs

# Perform similarity search
def search_jobs(query, index, job_descriptions, jobs, top_k=5):
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding, dtype=np.float32), top_k)
    return [jobs[i] for i in indices[0] if i < len(jobs)]

# Process query with Gemini AI
def process_with_gemini(query, index, job_descriptions, jobs):
    # Correct the query using TextBlob
    corrected_query = str(TextBlob(query).correct())  # Correct the input query
    
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
        "contents": [{"parts": [{"text": prompt}]}],
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

# Load job data and create the FAISS index when the app starts
job_data = fetch_job_data()
index, job_descriptions, jobs = (None, None, None)

if job_data:
    index, job_descriptions, jobs = create_faiss_index(job_data)

# API Endpoint: Chatbot Query Processing
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get("query", "")

    if not query:
        return jsonify({"response": "Please provide a query."})

    # Use the chatbot process to get a response from Gemini
    response = process_with_gemini(query, index, job_descriptions, jobs)
    return jsonify({"response": response})

# API Endpoint: Refresh Job Data from CouchDB
@app.route('/fetch_jobs', methods=['GET'])
def fetch_jobs():
    global job_data, index, job_descriptions, jobs
    job_data = fetch_job_data()

    if job_data:
        index, job_descriptions, jobs = create_faiss_index(job_data)
        flash("Job data successfully fetched!", "success")
        return jsonify({"message": "Job data refreshed successfully."})
    else:
        return jsonify({"message": "Failed to refresh job data."})

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
