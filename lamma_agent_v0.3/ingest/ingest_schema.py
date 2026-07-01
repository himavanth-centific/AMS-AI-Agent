import os
import oracledb
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 1. Load credentials
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# 2. File Path to your ALIPS Schema
# Update this if your schema text file is named or located differently!
SCHEMA_FILE_PATH = "assets/db_schema.txt" 

print("1. Initializing Embedding Model (all-MiniLM-L12-v2)...")
embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2")

print("2. Connecting to Oracle Database...")
try:
    conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    
    # Connect to the table we just created
    vector_store = OracleVS(
        client=conn,
        embedding_function=embed_model,
        table_name="alips_schema_docs",
        distance_strategy="COSINE"
    )

    print(f"3. Reading schema file from {SCHEMA_FILE_PATH}...")
    with open(SCHEMA_FILE_PATH, 'r', encoding='utf-8') as file:
        schema_text = file.read()

    print("4. Chunking the schema intelligently...")
    # This splitter is optimized for code/SQL. It tries to keep blocks together.
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\nCREATE TABLE", "\nCREATE PROCEDURE", "\n\n", "\n", " "],
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.create_documents([schema_text])
    print(f"   -> Schema broken down into {len(chunks)} searchable chunks.")

    print("5. Vectorizing and uploading to Oracle... (This may take a few minutes)")
    # Clear out the test document from earlier to keep things clean
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE alips_schema_docs") 
    
    # Upload the new real chunks
    vector_store.add_documents(chunks)
    
    print("\nSUCCESS! Your entire ALIPS schema is now vectorized and stored inside Oracle 23ai.")

except FileNotFoundError:
    print(f"\nERROR: Could not find your schema file at '{SCHEMA_FILE_PATH}'. Please check the path.")
except Exception as e:
    print(f"\nAn error occurred:\n{str(e)}")
finally:
    if 'conn' in locals():
        conn.close()