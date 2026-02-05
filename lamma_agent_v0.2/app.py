import sys
import os
from flask import Flask, render_template, request, jsonify
import ollama
import json
import re

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'actions'))
from actions import ACTION_MAP
from dbactions import execute_mssql_query

app = Flask(__name__)
    
def load_context():
    try:
        schema_path = "assets/db_schema_pruned.txt" if os.path.exists("assets/db_schema_pruned.txt") else "assets/db_schema.txt"
        with open(schema_path, "r", encoding="utf-8") as f:
            # schema = f.read()[:8000]
            schema = ""
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
            
        return prompt_template.replace("{schema_content}", schema)
    except Exception as e:
        return f"Error loading context: {str(e)}"

FULL_SYSTEM_PROMPT = load_context()

# def extract_json(text):
#     try:
#         match = re.search(r'\{.*\}', text, re.DOTALL)
#         return json.loads(match.group()) if match else None
#     except:
#         return None

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
    pending_sql = data.get("pending_sql")

    if pending_sql and user_input.lower() in ['yes', 'y', 'correct', 'execute']:
        result = execute_mssql_query(pending_sql)
        return jsonify({
            "response": "**Success!** Query executed. Results are shown below:",
            "data_table": result,
            "pending_sql": None
        })

    print( '***Calling Llama - ', user_input )
    response = ollama.chat(
        # model='alips-agent',
        model='llama3.2',
        messages=[
            {'role': 'system', 'content': FULL_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_input}
        ],
        # messages=[{'role': 'user', 'content': user_input}],
        options={'temperature': 0}
    )
    print( '***Llama response - ', response )

    raw_content = response['message']['content'].strip()
    data = extract_json(raw_content)
    
    ai_msg = raw_content
    exec_msg = ""
    sql_to_confirm = None

    if data:
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
    app.run(debug=True, port=5000, use_reloader=False)