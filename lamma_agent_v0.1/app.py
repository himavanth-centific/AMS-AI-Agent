import sys
import os
from flask import Flask, render_template, request, jsonify
import ollama
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from actions import ACTION_MAP

app = Flask(__name__)

SYSTEM_PROMPT = """
You are a high-security System Automation Agent. You translate user requests into JSON tool calls.

1. AVAILABLE TOOLS (ONLY these are allowed):
   - {"action": "open_browser", "args": "site_name"}
     - Example: "Open Instagram" -> {"action": "open_browser", "args": "instagram"}
   
   - {"action": "create_file", "args": {"filename": "name.txt", "folder": ".", "content": "text"}}
     - RULE: If no folder is mentioned, use "."
   
   - {"action": "open_cmd", "args": "command"}
     - RULE: For multiple Windows commands, use the '&' operator (Example: "cd /d d: & mkdir myfolder").
     - RULE: Wrap all file paths containing spaces in double quotes.

2. CRITICAL CONSTRAINTS (Hallucination Prevention):
   - If the user says something that does NOT clearly map to the tools above (e.g., "test", "hello", "tell me a joke"), you MUST return ONLY: {"action": "none", "args": "I am a system assistant. I can only open the browser, CMD, or create files."}
   - NEVER guess a URL if the user doesn't specify one. 
   - NEVER invent new tools or functions.
   - DO NOT provide any conversational text outside of the JSON block.

3. RESPONSE FORMAT:
   - Return ONLY raw JSON. No markdown backticks (```), no "Here is the JSON", just the {} object.
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'system', 'content': SYSTEM_PROMPT},
                  {'role': 'user', 'content': user_input}]
    )
    
    ai_msg = response['message']['content']
    exec_msg = ""

    if "{" in ai_msg:
        try:
            start = ai_msg.find("{")
            end = ai_msg.rfind("}") + 1
            data = json.loads(ai_msg[start:end])
            
            action = data.get("action")
            args = data.get("args")
            
            if action == "none":
                ai_msg = args
            elif action in ACTION_MAP:
                exec_msg = ACTION_MAP[action](args) if args else ACTION_MAP[action]()
                ai_msg = f"✅ Task executed: {action}"
            else:
                ai_msg = "I'm sorry, I don't recognize that command."

        except Exception as e:
            exec_msg = f"Processing Error: {str(e)}"

    return jsonify({"response": ai_msg, "execution": exec_msg})

if __name__ == '__main__':
    app.run(debug=True, port=5000)