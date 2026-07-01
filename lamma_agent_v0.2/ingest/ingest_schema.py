import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration
SCHEMA_FILE = "./db_schema.txt" 
DB_DIRECTORY = "./chroma_db"

def ingest():
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: {SCHEMA_FILE} not found.")
        return

    print("--- 1. Loading Schema File ---")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("--- 2. Chunking Text (Keeping Definitions Intact) ---")
    # We split by 'CREATE' so each table/procedure stays as one block
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
        separators=["CREATE TABLE", "CREATE PROCEDURE", "\n\n"]
    )
    docs = text_splitter.create_documents([raw_text])
    print(f"Created {len(docs)} chunks.")

    print("--- 3. Vectorizing Chunks (CPU Optimized) ---")
    # This 80MB model runs perfectly on 4GB RAM
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("--- 4. Saving to Local Vector DB ---")
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=DB_DIRECTORY
    )
    
    print(f"✅ Success! Vector DB ready at {DB_DIRECTORY}")

if __name__ == "__main__":
    print("--- 0. Start ---")
    ingest()