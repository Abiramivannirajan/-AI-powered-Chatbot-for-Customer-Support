import requests
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from rapidfuzz import process #string matching 
#Fetching data from couch
# CouchDB Credentials
COUCHDB_URL = "https://192.168.57.185:5984"
DB_NAME = "dpg_chatbot"
VIEW_JOBDETAILS = "jobdetails_by_id"
USERNAME = "d_couchdb"
PASSWORD = "Welcome#2"

# Load Two NLP Models for Better Accuracy
model_1 = SentenceTransformer("paraphrase-MiniLM-L6-v2")  
model_2 = SentenceTransformer("distilbert-base-nli-mean-tokens")

requests.packages.urllib3.disable_warnings()

def fetch_data(view_name):
    """Fetch data from CouchDB view."""
    try:
        response = requests.get(
            f"{COUCHDB_URL}/{DB_NAME}/_design/view/_view/{view_name}",
            auth=(USERNAME, PASSWORD),
            verify=False
        )
        response.raise_for_status()
        data = response.json()

        if "rows" not in data or not data["rows"]:
            return []

        documents = []
        for row in data["rows"]:
            doc_id = row.get("id")
            doc_response = requests.get(
                f"{COUCHDB_URL}/{DB_NAME}/{doc_id}",
                auth=(USERNAME, PASSWORD),
                verify=False
            )
            doc_response.raise_for_status()
            documents.append(doc_response.json())

        return documents
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {view_name}: {e}")
        return []

def process_data(documents):
    """Convert job postings into Q&A format, including job-specific and district-based questions."""
    qa_data = []
    district_jobs = {}
    company_roles = {}

    for doc in documents:
        data = doc.get("data", {})
        if not data:
            continue

        company = data.get("companyName", "").strip()
        location = data.get("location", "").strip().title()
        job_role = data.get("jobRole", "").strip()
        email = data.get("email", "").strip()
        apply_link = data.get("applyLink", "").strip()
        description = data.get("description", "").strip()
        experience = data.get("experience", "").strip()
        salary = data.get("salary", "").strip()

        if company and job_role:
            if company not in company_roles:
                company_roles[company] = []
            company_roles[company].append(job_role)

        if company:
            qa_data.append({"question": f"What is {company}?", "answer": description})
            qa_data.append({"question": f"Where is {company} located?", "answer": location})
            qa_data.append({"question": f"What experience is required  {company}?", "answer": experience})
            qa_data.append({"question": f"salary package  {company}?", "answer":  salary})

        if company and apply_link:
            qa_data.append({
                "question": f"How do I apply for a job  {company}?",
                "answer": f"**Job Role:** {job_role}\n**Email:** {email}\n**Apply Here:** {apply_link}"
            })

        if location:
            if location not in district_jobs:
                district_jobs[location] = []
            district_jobs[location].append(company)

    for location, companies in district_jobs.items():
        company_list = ", ".join(companies)
        qa_data.append({
            "question": f"List jobs  {location}",
            "answer": f"Companies hiring  {location}: {company_list}."
        })
        qa_data.append({
            "question": f"Show job openings  {location}",
            "answer": f"Available companies  {location}: {company_list}."
        })

    for company, roles in company_roles.items():
        role_list = ", ".join(roles)
        qa_data.append({
            "question": f"What job roles are available {company}?",
            "answer": f"Available roles {company}: {role_list}."
        })
        qa_data.append({
            "question": f"roles in {company}?",
            "answer": f"Available roles  {company}: {role_list}."
        })
    
    return qa_data

def save_to_json(data, filename="chatbot_dataset.json"):
    """Save processed data to JSON."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def train_chatbot():
    """Train chatbot by creating embeddings from stored dataset."""
    try:
        with open("chatbot_dataset.json", "r") as file:
            dataset = json.load(file)
    except FileNotFoundError:
        return

    questions = [item["question"] for item in dataset]
    
    embeddings_1 = model_1.encode(questions)
    embeddings_2 = model_2.encode(questions)
    
    np.save("embeddings_1.npy", embeddings_1)
    np.save("embeddings_2.npy", embeddings_2)

def update_chatbot():
    """Update chatbot if new data is available."""
    job_data = fetch_data(VIEW_JOBDETAILS)
    if not job_data:
        print("No job data retrieved from CouchDB. Please check database connection.")
        return
    
    qa_data = process_data(job_data)
    save_to_json(qa_data)
    train_chatbot()

def find_best_match(user_input):
    """Find the best matching question from the dataset using both models."""
    try:
        with open("chatbot_dataset.json", "r") as file:
            dataset = json.load(file)
    except FileNotFoundError:
        return "No data available. Train chatbot first."

    questions = [item["question"] for item in dataset]
    answers = [item["answer"] for item in dataset]

    if not questions:
        return "No trained data available."
    
    if not os.path.exists("embeddings_1.npy") or not os.path.exists("embeddings_2.npy"):
        return "Embeddings not found. Please train the chatbot first."
    
    embeddings_1 = np.load("embeddings_1.npy")
    embeddings_2 = np.load("embeddings_2.npy")

    input_embedding_1 = model_1.encode([user_input])
    input_embedding_2 = model_2.encode([user_input])

    similarity_1 = np.dot(embeddings_1, input_embedding_1.T).flatten()
    similarity_2 = np.dot(embeddings_2, input_embedding_2.T).flatten()

    best_idx_1 = np.argmax(similarity_1)
    best_idx_2 = np.argmax(similarity_2)

    if similarity_1[best_idx_1] > similarity_2[best_idx_2]:
        return answers[best_idx_1] if similarity_1[best_idx_1] > 0.75 else "Sorry, I don't understand that."
    else:
        return answers[best_idx_2] if similarity_2[best_idx_2] > 0.75 else "Sorry, I don't understand that."

def list_all_companies(documents):
    """List all companies with job roles."""
    all_companies = []

    for doc in documents:
        data = doc.get("data", {})
        if not data:
            continue

        company = data.get("companyName", "").strip()

        # If company exists, add it to the list
        if company:
            all_companies.append(company)

    return list(set(all_companies))  # Remove duplicates by converting to set and back to list

def chatbot_terminal():
    """Run chatbot in terminal mode."""
    print("\nChatbot is ready! Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Exiting chatbot. Have a great day!")
            break

        response = find_best_match(user_input)
        print("Chatbot:", response)

def main():
    """Main function to update and run chatbot."""
    update_chatbot()

    # Get the list of all companies with job roles
    job_data = fetch_data(VIEW_JOBDETAILS)
    if job_data:
        all_companies = list_all_companies(job_data)
        print("Companies hiring:")
        for company in all_companies:
            print(company)
    else:
        print("No job data retrieved from CouchDB.")

    chatbot_terminal()

if __name__ == "__main__":
    main()


# import streamlit as st 
# import google.generativeai as genai 


# genai.configure(api_key="AIzaSyArdQA4hsN0rlUJLBT09bDbR0UPaaYryhY")  


# def get_gemini_response(user_input): 
#     """Generate a structured, precise response using Gemini API with advanced prompting."""

#     prompt = f"""
#     You are an expert career counselor assisting students with their education and job queries. 
#     Provide **accurate, structured, and to-the-point responses** in a **step-by-step manner**.

#     **Guidelines for Response:**
#     - Keep answers **precise and structured** (no generic responses).
#     - Use **bullet points or step-by-step breakdowns**.
#     - **If the question is about higher education**, suggest courses based on eligibility, entrance exams, and future job scope.
#     - **If the question is about career paths**, provide job roles, industries, salaries, and required skills.
#     - **If the question is about entrance exams**, list eligibility, syllabus, and exam dates.
#     - **If the question is about a confused student**, give **motivational and clear** guidance.
#     - **If the user asks about multiple fields**, compare them with advantages and disadvantages.
    
#     **Example Response Structure:**
#      **Available Courses:** List top courses based on the student’s stream.  
#      **Entrance Exams:** Mention exams required for admission.  
#      **Job Opportunities:** List job roles, industries, salary trends.  
#      **Future Scope:** Explain growth trends and industry demand.  

#     **Student's Question:** {user_input}
#     """

#     model = genai.GenerativeModel("gemini-1.5-flash")
#     response = model.generate_content(prompt)

#     return response.text if response.text else "Sorry, I couldn't generate a precise response."

 
# st.title("Career Guidance Chatbot")
# st.write("Get precise answers about courses, job opportunities, and career choices!")


# user_input = st.text_input("Type your question here:")

# if user_input:
#     response = get_gemini_response(user_input)
#     st.write("**Bot:**", response)


