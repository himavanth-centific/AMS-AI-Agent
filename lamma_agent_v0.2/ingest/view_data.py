from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Setup the same embedding model used during ingestion
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Load the existing database from your local folder
vector_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings
)

# 3. Get all data from the database
# This retrieves the raw text chunks stored in the DB
data = vector_db.get()

print(f"--- Database Summary ---")
print(f"Total Chunks Stored: {len(data['documents'])}")
print("-" * 30)

# 4. Print the first 5 chunks to verify
for i in range(min(5, len(data['documents']))):
    print(f"CHUNK #{i+1}:")
    print(data['documents'][i]) # Print first 500 characters
    print("-" * 30)