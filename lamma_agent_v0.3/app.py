import sys
import os
from flask import Flask, render_template, request, jsonify
import ollama
import json
import re
import oracledb
from dotenv import load_dotenv

# Native Oracle AI Vector Store & HF Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'actions'))
from actions import ACTION_MAP
from dbactions import execute_mssql_query

app = Flask(__name__)

# --- LOAD SECRETS ---
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# --- INITIALIZE RAG ONCE ---
# Initialize the upgraded embedding model globally so it doesn't reload on every question
print("Waking up Oracle integration and embedding model...")
EMBED_MODEL = HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2")

def get_context(user_query):
    conn = None
    try:
        # 1. Connect to Oracle 23ai
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        
        # 2. Hook up LangChain to your existing vectorized schema table
        vector_store = OracleVS(
            client=conn,
            embedding_function=EMBED_MODEL,
            table_name="alips_schema_docs",
            distance_strategy="COSINE"
        )
        
        # 3. Perform the vector similarity search directly inside Oracle
        docs = vector_store.similarity_search(user_query, k=4)
        context = "\n\n".join([d.page_content for d in docs])

        # 4. FALLBACK: Keyword Logic for the Demo
        # If RAG returns nothing, we manually look for keywords
        if not context.strip():
            print("!!! RAG empty - using Keyword Fallback !!!")
            keywords = {
                "invoice": "Table: BilledInvoiceInfos (inv_no, ac_no, bill_amt)\nSP: sp_GetAllInvoices",
                "customer": "Table: CustomerProfiles (AccountNumber, cny_cd)",
                "shipment": "Table: BilledInvoiceShipments (track_no, inv_no)"
            }
            for key, val in keywords.items():
                if key in user_query.lower():
                    context += f"\n{val}"
                    
        return context
    except Exception as e:
        print(f"Oracle Retrieval Error: {e}")
        return ""
    finally:
        # Guarantee connection closes even if an error occurs
        if conn:
            conn.close()
    
def load_prompt_template():
    """Loads the system prompt text WITHOUT replacing the schema tag yet."""
    try:
        # We load the template only. We'll swap {schema_content} during the chat.
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return "MANDATORY: Respond ONLY in JSON."

# Store the raw template as a global variable
BASE_PROMPT_TEMPLATE = load_prompt_template()

def extract_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match: return None
        clean_text = match.group().replace('\\u0027', "'").replace('\\n', ' ')
        return json.loads(clean_text)
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print("---------------------*** Query Start ***-------------------------------")
    data = request.json
    user_input = data.get("message", "")
    history = data.get("history", [])
    pending_sql = data.get("pending_sql")

    # 1. SQL Execution Confirmation
    if pending_sql and user_input.lower() in ['yes', 'y', 'correct', 'execute']:
        result = execute_mssql_query(pending_sql)
        return jsonify({
            "response": "**Success!** Query executed. Results are shown below:",
            "data_table": result,
            "pending_sql": None
        })

    # 2. RAG RETRIEVAL: Find the specific tables for THIS question
    print(f"*** Searching Oracle schema for: {user_input}")
    retrieved_schema = get_context(user_input)
    
    # 3. DYNAMIC PROMPT: Inject the found schema into your specific template
    final_prompt = BASE_PROMPT_TEMPLATE.replace("{schema_content}", retrieved_schema)
    print(retrieved_schema, '\n\n\n', final_prompt)
    
    messages = [{'role': 'system', 'content': final_prompt}]
    
    for turn in history:
        messages.append({'role': 'user', 'content': turn['user']})
        messages.append({'role': 'assistant', 'content': turn['ai']})
    
    messages.append({'role': 'user', 'content': user_input})   
     
    # 4. CALL LLAMA 
    print(f"*** Calling Llama...")
    try:
        response = ollama.chat(
            model='llama3.2', 
            messages=messages,
            options={
                "temperature": 0.0, # Flexibility - Need to check how 0.1 and 0.2 behaves
                "num_ctx": 4096,     # Have to test with higher ram allowance
                "top_p": 0.9, # Token sampling accuracy
                "repeat_penalty": 1.1
            }
        )
    except Exception as e:
        print(f"Ollama Error: {e}")
        return jsonify({"response": "I'm having trouble accessing my brain right now. Is Ollama running?"})

    raw_content = response['message']['content'].strip()
    print(f"*** Llama output: {raw_content}")
    data = extract_json(raw_content)
    
    ai_msg = raw_content
    exec_msg = ""
    sql_to_confirm = None

    if data:
        # Detect SQL anywhere in the response
        detected_sql = None
        if "sql" in str(data):
            if "args" in data and isinstance(data["args"], dict):
                detected_sql = data["args"].get("sql")
            elif "sql" in data:
                detected_sql = data["sql"]

        if detected_sql:
            sql_to_confirm = detected_sql
            ai_msg = f"**I have prepared the following script:**\n\n`{sql_to_confirm}`\n\n**Do you want to execute these changes? (Yes/No)**"
        
        elif data.get("action") in ACTION_MAP:
            action = data.get("action")
            args = data.get("args")
            exec_msg = ACTION_MAP[action](args) if args else ACTION_MAP[action]()
            
            if action == "open_browser":
                ai_msg = f"Opening **{args}** in your browser..."
            elif action == "open_cmd":
                ai_msg = f"Running command in **CMD**."
            else:
                ai_msg = f"Task executed: **{action}**"
        
        elif data.get("action") == "none":
            ai_msg = data.get("args") if data.get("args") else raw_content
            
    elif raw_content and "{}" not in raw_content:
        ai_msg = raw_content
                   
    print("---------------------*** Query Ends ***-------------------------------")

    return jsonify({
        "response": ai_msg, 
        "execution": exec_msg,
        "pending_sql": sql_to_confirm
    })

if __name__ == '__main__':
    # No reloader to prevent double-loading of the model in RAM
    app.run(debug=True, port=5000, use_reloader=False)