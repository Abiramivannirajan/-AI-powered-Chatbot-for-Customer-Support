import pandas as pd
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download nltk package
nltk.download('punkt', quiet=True)

def load_csv(file_path):
    """Load the CSV file and extract Questions & Answers"""
    try:
        # Try reading the CSV file with utf-8 encoding and comma delimiter
        df = pd.read_csv(file_path, header=0, encoding='utf-8', delimiter=',')  
        
        print("Columns found:", df.columns)  # Debugging
        
        # Check if the CSV file has exactly two columns: Question and Answer
        if df.shape[1] != 2:
            raise ValueError("CSV file must contain exactly two columns: Question and Answer.")
        
        # Strip extra spaces in case there's any unnecessary whitespace in the column names
        df.columns = df.columns.str.strip()

        questions = df['Question'].astype(str).tolist()
        answers = df['Answer'].astype(str).tolist()
        return questions, answers

    except FileNotFoundError:
        print("Error: File not found. Please check the file path.")
        exit()
    except pd.errors.ParserError:
        print("Error: There was an issue parsing the CSV file. Please check the format.")
        exit()
    except ValueError as e:
        print(e)
        exit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit()

def find_best_answer(user_input, questions, answers):
    """Finds the best-matching answer using TF-IDF & cosine similarity"""
    questions.append(user_input)  # Add user query to compare
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(questions)
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    best_match_index = similarity_scores.argmax()
    
    if similarity_scores.max() == 0:  # No match found
        return "I apologize, I don't understand."
    
    return answers[best_match_index]

def chatbot():
    """Runs the chatbot interaction loop"""
    file_path = input("Enter the path to the CSV file: ")
    questions, answers = load_csv(file_path)
    
    print("Doc Bot: I am Doctor Bot. Ask me anything about the uploaded topics. Type 'bye' to exit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'bye', 'quit']:
            print("Doc Bot: Chat with you later!")
            break
        else:
            response = find_best_answer(user_input, questions, answers)
            print(f"Doc Bot: {response}")

# Run the chatbot
if __name__ == "__main__":
    chatbot()
