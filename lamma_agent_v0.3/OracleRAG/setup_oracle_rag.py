import os
import oracledb
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_core.documents import Document

# 1. Load credentials
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

print("1. Connecting to Oracle Database...")
try:
    conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    print("   Connection Successful!")

    # 2. Initialize the upgraded model in Python (instead of inside Oracle)
    print("2. Downloading/Loading upgraded embedding model in Python...")
    embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2")
    
    # 3. Create the Oracle Vector Store Table
    print("3. Initializing Oracle Vector Store table (alips_schema_docs)...")
    
    # LangChain's OracleVS will automatically create the table if it doesn't exist!
    vector_store = OracleVS(
        client=conn,
        embedding_function=embed_model,
        table_name="alips_schema_docs",
        distance_strategy="COSINE"
    )
    
    # 4. Run a quick validation test
    print("4. Testing the pipeline with a sample document...")
    test_doc = [Document(page_content="This is a test of the Oracle RAG pipeline.", metadata={"source": "test"})]
    
    # Python calculates the vector, then sends it to Oracle for storage
    vector_store.add_documents(test_doc)
    
    # Verify Oracle can search it
    results = vector_store.similarity_search("Oracle RAG test", k=1)
    
    print("\nSUCCESS! Pipeline is fully operational.")
    print("Test Search Result Match:", results[0].page_content)

except Exception as e:
    print(f"\nAn error occurred:\n{str(e)}")
finally:
    if 'conn' in locals():
        conn.close()