
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

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

# Save embeddings
np.save('embeddings.npy', embeddings)

# Confirm dataset size
print(f"Total questions in dataset: {len(df)}")
print(f"Shape of embeddings: {embeddings.shape}")
