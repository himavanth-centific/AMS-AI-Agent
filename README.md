# AMS-AI-Agent

Install Ollama

Ollama pull llama3.2  (OR) Ollama run llama3.2 "Hi"

cd .\lamma_agent_v0.3\

pip install ollama flask pyodbc pandas

pip install flask ollama langchain-huggingface langchain-community chromadb sentence-transformers

-- ollama create alips-agent -f Modelfile -- Not required

--------------------------------       V0.3       ---------------------------------

Install Oracle 26ai free eddition - [www.oracle.com/database/free/get-started/#windows](https://www.oracle.com/database/free/get-started/#windows)

pip install oracledb langchain-community langchain-core

OracleDB setup - cmd :

    - sqlplus / as sysdba

    - ALTER USER SYSTEM IDENTIFIED BY MySecurePassword123;

    - ALTER SESSION SET CONTAINER = FREEPDB1;

    - CREATE OR REPLACE DIRECTORY VECTOR_MODEL_DIR AS 'C:\Users\vhima\Documents\AMS-AI-Agent\lamma_agent_v0.3\OracleModels';

    - GRANT CREATE MINING MODEL TO SYSTEM;

    - exit

All Mini setup - powershell :

    - New-Item -ItemType Directory -Force -Path "C:\Users\vhima\Documents\AMS-AI-Agent\lamma_agent_v0.3\OracleModels"

    - Invoke-WebRequest -Uri "https://adwc4pm.objectstorage.us-ashburn-1.oci.customer-oci.com/p/eLddQappgBJ7jNi6Guz9m9LOtYe2u8LWY19GfgU8flFK4N9YgP4kTlrE9Px3pE12/n/adwc4pm/b/OML-Resources/o/all_MiniLM_L12_v2.onnx" -OutFile "C:\Users\vhima\Documents\AMS-AI-Agent\lamma_agent_v0.3\OracleModels\all_MiniLM_L12_v2.onnx"

Make sure OracleModels have folder permissions and repeate - the obove sqlplus cmd step.

pip install oracledb python-dotenv
pip install oracledb langchain-community langchain-huggingface sentence-transformers

python OracleRAG/setup_oracle_rag.py

python ingest/ingest_schema.py

Python app.py
