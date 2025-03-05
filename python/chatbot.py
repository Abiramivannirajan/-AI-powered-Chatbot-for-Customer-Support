
# import requests
# import json
# import numpy as np
# import time
# from sentence_transformers import SentenceTransformer
# from rapidfuzz import process

# # CouchDB Credentials
# COUCHDB_URL = "https://192.168.57.185:5984"
# DB_NAME = "dpg_chatbot"
# VIEW_STREAM = "stream_by_id"
# VIEW_SUBSTREAM = "substream_by_streamid"
# VIEW_JOBDETAILS = "jobdetails_by_id"
# USERNAME = "d_couchdb"
# PASSWORD = "Welcome#2"

# # Load NLP Model
# model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
# # Disable SSL warnings (for development)
# requests.packages.urllib3.disable_warnings()

# # Store last known document count
# last_known_count = 0

# def fetch_data(view_name):
#     """Fetch data from CouchDB."""
#     try:
#         response = requests.get(
#             f"{COUCHDB_URL}/{DB_NAME}/_design/view/_view/{view_name}",
#             auth=(USERNAME, PASSWORD),
#             verify=False
#         )
#         response.raise_for_status()
#         data = response.json()

#         if "rows" not in data or not data["rows"]:
#             print(f"No data found in {view_name}.")
#             return []

#         documents = []
#         for row in data["rows"]:
#             doc_id = row.get("id")
#             doc_response = requests.get(
#                 f"{COUCHDB_URL}/{DB_NAME}/{doc_id}",
#                 auth=(USERNAME, PASSWORD),
#                 verify=False
#             )
#             doc_response.raise_for_status()
#             documents.append(doc_response.json())

#         return documents
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching {view_name}: {e}")
#         return []

# def process_data(documents, data_type):
#     """Process CouchDB data into chatbot Q&A format."""
#     qa_data = []
#     for doc in documents:
#         data = doc.get("data", {})
#         if not data:
#             continue

#         if data_type == "stream":
#             name = data.get("stream_Name")
#             description = data.get("description")
#             if name and description:
#                 qa_data.append({"question": f"What is {name}?", "answer": description})
        
#         elif data_type == "substream":
#             name = data.get("substream_Name")
#             stream_name = data.get("stream_Name", "its field")
#             description = data.get("description")
#             if name and description:
#                 qa_data.append({"question": f"What is {name} in {stream_name}?", "answer": description})

#         elif data_type == "job":
#             company = data.get("companyName", "").strip()
#             location = data.get("location", "").strip()
#             job_role = data.get("jobRole", "").strip()
#             email = data.get("email", "").strip()
#             apply_link = data.get("applyLink", "").strip()
#             description = data.get("description", "").strip()
#             experience = data.get("experience", "").strip()
#             salary = data.get("salary", "").strip()
            
#             if company:
#                 qa_data.append({"question": f"What is {company}?", "answer": description})
#                 qa_data.append({"question": f"Where is {company} located?", "answer": location})
#                 qa_data.append({"question": f"What experience is required for {company}?", "answer": experience})
#                 qa_data.append({"question": f"What is the salary for {company}?", "answer": salary})
            
#             if company and apply_link:
#                 qa_data.append({
#                     "question": f"How do I apply for a job at {company}?",
#                     "answer": f"**Job Role:** {job_role}\n**Email:** {email}\n**Apply Here:** {apply_link}"
#                 })
        
#     print(f"Processed {len(qa_data)} {data_type} questions.")
#     return qa_data

# def process_data(documents):
#     """Convert job postings into Q&A format and dynamically add district-based job listings with only company names."""
#     qa_data = []
#     district_jobs = {}  # Dictionary to store companies by location

#     for doc in documents:
#         data = doc.get("data", {})
#         if not data:
#             continue

#         company = data.get("companyName", "").strip()
#         location = data.get("location", "").strip().title()  # Normalize district names

#         if company and location:
#             if location not in district_jobs:
#                 district_jobs[location] = []
#             district_jobs[location].append(company)

#     #  Add questions dynamically for each district
#     for location, companies in district_jobs.items():
#         company_list = ", ".join(companies)  # Format company names
#         qa_data.append({
#             "question": f"List jobs in {location}",
#             "answer": f"Companies hiring in {location}: {company_list}."
#         })
#         qa_data.append({
#             "question": f"Show job openings in {location}",
#             "answer": f"Available companies in {location}: {company_list}."
#         })

#     return qa_data


# def save_to_json(data, filename="chatbot_dataset.json"):
#     """Save Q&A data to JSON file."""
#     with open(filename, "w") as file:
#         json.dump(data, file, indent=4)
#     print(f"Chatbot dataset saved to {filename}")

# def train_chatbot():
#     """Train chatbot by generating embeddings."""
#     try:
#         with open("chatbot_dataset.json", "r") as file:
#             dataset = json.load(file)
#     except FileNotFoundError:
#         print("Dataset not found! Run data fetching first.")
#         return

#     questions = [item["question"] for item in dataset]
#     embeddings = model.encode(questions)
#     np.save("embeddings.npy", embeddings)
#     print("Chatbot training completed! Embeddings saved.")

# def update_chatbot():
#     """Fetch latest data, check for updates, and train chatbot."""
#     global last_known_count
#     print("Checking for new data updates in CouchDB...")

#     stream_data = fetch_data(VIEW_STREAM)
#     substream_data = fetch_data(VIEW_SUBSTREAM)
#     job_data = fetch_data(VIEW_JOBDETAILS)

#     total_count = len(stream_data) + len(substream_data) + len(job_data)
#     if total_count == last_known_count:
#         print("No new updates found. Skipping training.")
#         return

#     last_known_count = total_count
#     qa_data = process_data(stream_data, "stream") + process_data(substream_data, "substream") + process_data(job_data, "job")
#     save_to_json(qa_data)
#     train_chatbot()

# def find_best_match(user_input, questions):
#     """Finds the best-matching question."""
#     best_match, score, index = process.extractOne(user_input, questions, score_cutoff=75)
#     return index if index is not None else -1

# def chatbot_terminal():
#     """Run interactive chatbot in terminal."""
#     print("\nChatbot is ready! Type 'exit' to quit.\n")
#     while True:
#         try:
#             with open("chatbot_dataset.json", "r") as file:
#                 dataset = json.load(file)
#             if not dataset:
#                 print("No data found. Exiting chatbot.")
#                 break

#             questions = [item["question"] for item in dataset]
#             answers = [item["answer"] for item in dataset]
#             embeddings = np.load("embeddings.npy")
#         except FileNotFoundError:
#             print("Dataset or embeddings missing. Train chatbot first.")
#             break

#         user_input = input("You: ").strip()
#         if user_input.lower() == "exit":
#             print("Exiting chatbot. Have a great day!")
#             break

#         best_match_index = find_best_match(user_input, questions)
#         if best_match_index == -1:
#             print("Chatbot: Sorry, I don't understand that.")
#         else:
#             print(f"Chatbot: {answers[best_match_index]}")

# def main():
#     update_chatbot()
#     chatbot_terminal()

# if __name__ == "__main__":
#     main()
# import requests
# import json
# import numpy as np
# import os
# from sentence_transformers import SentenceTransformer
# from rapidfuzz import process

# # CouchDB Credentials
# COUCHDB_URL = "https://192.168.57.185:5984"
# DB_NAME = "dpg_chatbot"
# VIEW_JOBDETAILS = "jobdetails_by_id"
# USERNAME = "d_couchdb"
# PASSWORD = "Welcome#2"

# # Load Two NLP Models for Better Accuracy
# model_1 = SentenceTransformer("paraphrase-MiniLM-L6-v2")  
# model_2 = SentenceTransformer("distilbert-base-nli-mean-tokens")

# requests.packages.urllib3.disable_warnings()

# def fetch_data(view_name):
#     """Fetch data from CouchDB view."""
#     try:
#         response = requests.get(
#             f"{COUCHDB_URL}/{DB_NAME}/_design/view/_view/{view_name}",
#             auth=(USERNAME, PASSWORD),
#             verify=False
#         )
#         response.raise_for_status()
#         data = response.json()

#         if "rows" not in data or not data["rows"]:
#             return []

#         documents = []
#         for row in data["rows"]:
#             doc_id = row.get("id")
#             doc_response = requests.get(
#                 f"{COUCHDB_URL}/{DB_NAME}/{doc_id}",
#                 auth=(USERNAME, PASSWORD),
#                 verify=False
#             )
#             doc_response.raise_for_status()
#             documents.append(doc_response.json())

#         return documents
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching {view_name}: {e}")
#         return []

# def process_data(documents):
#     """Convert job postings into Q&A format and dynamically add district-based job listings with only company names."""
#     qa_data = []
#     district_jobs = {}  # Dictionary to store companies by location

#     for doc in documents:
#         data = doc.get("data", {})
#         if not data:
#             continue

#         company = data.get("companyName", "").strip()
#         location = data.get("location", "").strip().title()  # Normalize district names

#         if company and location:
#             if location not in district_jobs:
#                 district_jobs[location] = []
#             district_jobs[location].append(company)

#     #  Add questions dynamically for each district
#     for location, companies in district_jobs.items():
#         company_list = ", ".join(companies)  # Format company names
#         qa_data.append({
#             "question": f"List jobs in {location}",
#             "answer": f"Companies hiring in {location}: {company_list}."
#         })
#         qa_data.append({
#             "question": f"Show job openings in {location}",
#             "answer": f"Available companies in {location}: {company_list}."
#         })

#     return qa_data

# def save_to_json(data, filename="chatbot_dataset.json"):
#     """Save processed data to JSON."""
#     with open(filename, "w") as file:
#         json.dump(data, file, indent=4)

# def train_chatbot():
#     """Train chatbot by creating embeddings from stored dataset."""
#     try:
#         with open("chatbot_dataset.json", "r") as file:
#             dataset = json.load(file)
#     except FileNotFoundError:
#         return

#     questions = [item["question"] for item in dataset]
    
#     # Generate embeddings using both models
#     embeddings_1 = model_1.encode(questions)
#     embeddings_2 = model_2.encode(questions)
    
#     # Save both embeddings
#     np.save("embeddings_1.npy", embeddings_1)
#     np.save("embeddings_2.npy", embeddings_2)

# def update_chatbot():
#     """Update chatbot if new data is available."""
#     job_data = fetch_data(VIEW_JOBDETAILS)
#     if not job_data:
#         print("No job data retrieved from CouchDB. Please check database connection.")
#         return
    
#     qa_data = process_data(job_data)
#     save_to_json(qa_data)
#     train_chatbot()

# def find_best_match(user_input):
#     """Find the best matching question from the dataset using both models."""
#     try:
#         with open("chatbot_dataset.json", "r") as file:
#             dataset = json.load(file)
#     except FileNotFoundError:
#         return "No data available. Train chatbot first."

#     questions = [item["question"] for item in dataset]
#     answers = [item["answer"] for item in dataset]

#     if not questions:
#         return "No trained data available."
    
#     # Load both sets of embeddings
#     if not os.path.exists("embeddings_1.npy") or not os.path.exists("embeddings_2.npy"):
#         return "Embeddings not found. Please train the chatbot first."
    
#     embeddings_1 = np.load("embeddings_1.npy")
#     embeddings_2 = np.load("embeddings_2.npy")

#     # Get user input embedding from both models
#     input_embedding_1 = model_1.encode([user_input])
#     input_embedding_2 = model_2.encode([user_input])

#     # Compute cosine similarity for both models
#     similarity_1 = np.dot(embeddings_1, input_embedding_1.T).flatten()
#     similarity_2 = np.dot(embeddings_2, input_embedding_2.T).flatten()

#     # Find the highest score from both models
#     best_idx_1 = np.argmax(similarity_1)
#     best_idx_2 = np.argmax(similarity_2)

#     # Choose the answer with the highest confidence
#     if similarity_1[best_idx_1] > similarity_2[best_idx_2]:
#         return answers[best_idx_1] if similarity_1[best_idx_1] > 0.75 else "Sorry, I don't understand that."
#     else:
#         return answers[best_idx_2] if similarity_2[best_idx_2] > 0.75 else "Sorry, I don't understand that."

# def chatbot_terminal():
#     """Run chatbot in terminal mode."""
#     print("\nChatbot is ready! Type 'exit' to quit.\n")
#     while True:
#         user_input = input("You: ").strip()
#         if user_input.lower() == "exit":
#             print("Exiting chatbot. Have a great day!")
#             break

#         response = find_best_match(user_input)
#         print("Chatbot:", response)

# def main():
#     """Main function to update and run chatbot."""
#     update_chatbot()
#     chatbot_terminal()

# if __name__ == "__main__":
#     main()
# import requests
# import json
# import numpy as np
# import os
# from sentence_transformers import SentenceTransformer
# from rapidfuzz import process

# # CouchDB Credentials
# COUCHDB_URL = "https://192.168.57.185:5984"
# DB_NAME = "dpg_chatbot"
# VIEW_JOBDETAILS = "jobdetails_by_id"
# USERNAME = "d_couchdb"
# PASSWORD = "Welcome#2"

# # Load Two NLP Models for Better Accuracy
# model_1 = SentenceTransformer("paraphrase-MiniLM-L6-v2")  
# model_2 = SentenceTransformer("distilbert-base-nli-mean-tokens")

# requests.packages.urllib3.disable_warnings()

# def fetch_data(view_name):
#     """Fetch data from CouchDB view."""
#     try:
#         response = requests.get(
#             f"{COUCHDB_URL}/{DB_NAME}/_design/view/_view/{view_name}",
#             auth=(USERNAME, PASSWORD),
#             verify=False
#         )
#         response.raise_for_status()
#         data = response.json()

#         if "rows" not in data or not data["rows"]:
#             return []

#         documents = []
#         for row in data["rows"]:
#             doc_id = row.get("id")
#             doc_response = requests.get(
#                 f"{COUCHDB_URL}/{DB_NAME}/{doc_id}",
#                 auth=(USERNAME, PASSWORD),
#                 verify=False
#             )
#             doc_response.raise_for_status()
#             documents.append(doc_response.json())

#         return documents
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching {view_name}: {e}")
#         return []

# def process_data(documents):
#     """Convert job postings into Q&A format, including job-specific and district-based questions."""
#     qa_data = []
#     district_jobs = {}

#     for doc in documents:
#         data = doc.get("data", {})
#         if not data:
#             continue

#         company = data.get("companyName", "").strip()
#         location = data.get("location", "").strip().title()
#         job_role = data.get("jobRole", "").strip()
#         email = data.get("email", "").strip()
#         apply_link = data.get("applyLink", "").strip()
#         description = data.get("description", "").strip()
#         experience = data.get("experience", "").strip()
#         salary = data.get("salary", "").strip()

#         if company:
#             qa_data.append({"question": f"What is {company}?", "answer": description})
#             qa_data.append({"question": f"Where is {company} located?", "answer": location})
#             qa_data.append({"question": f"What experience is required for {company}?", "answer": experience})
#             qa_data.append({"question": f"What is the salary for {company}?", "answer": salary})

#         if company and apply_link:
#             qa_data.append({
#                 "question": f"How do I apply for a job at {company}?",
#                 "answer": f"**Job Role:** {job_role}\n**Email:** {email}\n**Apply Here:** {apply_link}"
#             })

#         if location:
#             if location not in district_jobs:
#                 district_jobs[location] = []
#             district_jobs[location].append(company)

#     for location, companies in district_jobs.items():
#         company_list = ", ".join(companies)
#         qa_data.append({
#             "question": f"List jobs in {location}",
#             "answer": f"Companies hiring in {location}: {company_list}."
#         })
#         qa_data.append({
#             "question": f"Show job openings in {location}",
#             "answer": f"Available companies in {location}: {company_list}."
#         })

#     return qa_data

# def save_to_json(data, filename="chatbot_dataset.json"):
#     """Save processed data to JSON."""
#     with open(filename, "w") as file:
#         json.dump(data, file, indent=4)

# def train_chatbot():
#     """Train chatbot by creating embeddings from stored dataset."""
#     try:
#         with open("chatbot_dataset.json", "r") as file:
#             dataset = json.load(file)
#     except FileNotFoundError:
#         return

#     questions = [item["question"] for item in dataset]
    
#     embeddings_1 = model_1.encode(questions)
#     embeddings_2 = model_2.encode(questions)
    
#     np.save("embeddings_1.npy", embeddings_1)
#     np.save("embeddings_2.npy", embeddings_2)

# def update_chatbot():
#     """Update chatbot if new data is available."""
#     job_data = fetch_data(VIEW_JOBDETAILS)
#     if not job_data:
#         print("No job data retrieved from CouchDB. Please check database connection.")
#         return
    
#     qa_data = process_data(job_data)
#     save_to_json(qa_data)
#     train_chatbot()

# def find_best_match(user_input):
#     """Find the best matching question from the dataset using both models."""
#     try:
#         with open("chatbot_dataset.json", "r") as file:
#             dataset = json.load(file)
#     except FileNotFoundError:
#         return "No data available. Train chatbot first."

#     questions = [item["question"] for item in dataset]
#     answers = [item["answer"] for item in dataset]

#     if not questions:
#         return "No trained data available."
    
#     if not os.path.exists("embeddings_1.npy") or not os.path.exists("embeddings_2.npy"):
#         return "Embeddings not found. Please train the chatbot first."
    
#     embeddings_1 = np.load("embeddings_1.npy")
#     embeddings_2 = np.load("embeddings_2.npy")

#     input_embedding_1 = model_1.encode([user_input])
#     input_embedding_2 = model_2.encode([user_input])

#     similarity_1 = np.dot(embeddings_1, input_embedding_1.T).flatten()
#     similarity_2 = np.dot(embeddings_2, input_embedding_2.T).flatten()

#     best_idx_1 = np.argmax(similarity_1)
#     best_idx_2 = np.argmax(similarity_2)

#     if similarity_1[best_idx_1] > similarity_2[best_idx_2]:
#         return answers[best_idx_1] if similarity_1[best_idx_1] > 0.75 else "Sorry, I don't understand that."
#     else:
#         return answers[best_idx_2] if similarity_2[best_idx_2] > 0.75 else "Sorry, I don't understand that."

# def chatbot_terminal():
#     """Run chatbot in terminal mode."""
#     print("\nChatbot is ready! Type 'exit' to quit.\n")
#     while True:
#         user_input = input("You: ").strip()
#         if user_input.lower() == "exit":
#             print("Exiting chatbot. Have a great day!")
#             break

#         response = find_best_match(user_input)
#         print("Chatbot:", response)

# def main():
#     """Main function to update and run chatbot."""
#     update_chatbot()
#     chatbot_terminal()

# if __name__ == "__main__":
#     main()
import requests
import json
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from rapidfuzz import process

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
            qa_data.append({"question": f"What experience is required for {company}?", "answer": experience})
            qa_data.append({"question": f"What is the salary for {company}?", "answer": salary})

        if company and apply_link:
            qa_data.append({
                "question": f"How do I apply for a job at {company}?",
                "answer": f"**Job Role:** {job_role}\n**Email:** {email}\n**Apply Here:** {apply_link}"
            })

        if location:
            if location not in district_jobs:
                district_jobs[location] = []
            district_jobs[location].append(company)

    for location, companies in district_jobs.items():
        company_list = ", ".join(companies)
        qa_data.append({
            "question": f"List jobs in {location}",
            "answer": f"Companies hiring in {location}: {company_list}."
        })
        qa_data.append({
            "question": f"Show job openings in {location}",
            "answer": f"Available companies in {location}: {company_list}."
        })

    for company, roles in company_roles.items():
        role_list = ", ".join(roles)
        qa_data.append({
            "question": f"What job roles are available at {company}?",
            "answer": f"Available roles at {company}: {role_list}."
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
    chatbot_terminal()

if __name__ == "__main__":
    main()
