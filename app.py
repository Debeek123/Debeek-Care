from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
from utils import *
import os
import json as pyjson
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a32f3b4c5e6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l'
CORS(app, resources={r"/chat": {"origins": "*"}})

CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'chat_sessions.json')

def load_chat_sessions():
    if not os.path.exists(CHAT_HISTORY_FILE):
        return {}
    with open(CHAT_HISTORY_FILE, 'r') as f:
        try:
            return pyjson.load(f)
        except Exception:
            return {}

def save_chat_sessions(sessions):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        pyjson.dump(sessions, f)

def get_or_create_session_id():
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

# Flask routes
@app.route('/chatbot')
def index():
    session_id = get_or_create_session_id()
    sessions = load_chat_sessions()
    if session_id not in sessions:
        sessions[session_id] = []
        save_chat_sessions(sessions)
    
    chat_history = sessions.get(session_id, [])



    return render_template('chatbot.html', chat_history=chat_history[1:])


@app.route('/chat', methods=['POST'])
def chating():

    user_input = request.json.get("message", "")
    location = request.json.get("location", "")

    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    session_id = get_or_create_session_id()
    sessions = load_chat_sessions()
    chat_history = sessions.get(session_id, [])

    if not chat_history:
        chat_history = [system_prompt]

    if location:
        chat_history.append({"role": "user", "content": f'''{{"user": "{user_input}", "location": {location}}}'''})
    else:
        chat_history.append({"role": "user", "content": f'''{{"user": "{user_input}"}}'''})
    
    chat_history = [
        msg for msg in chat_history
        if msg.get("content") is not None and str(msg.get("content")).strip() != ""
    ]

    response = chat(chat_history)


    if response.content:
        chat_history.append({"role": "assistant", "content": response.content})
        sessions[session_id] = chat_history
        save_chat_sessions(sessions)
        resp = make_response(jsonify({"reply": response.content}), 200)
        resp.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
        return resp
    
    for function_call in response.tool_calls:
        print(function_call)
        function_name = function_call.function.name
        print(f"Function arguments: {function_call.function.arguments}")
        print(type(function_call.function.arguments))
        arguments = pyjson.loads(function_call.function.arguments)
        print(f"Function call: {function_name} with arguments: {arguments}")
        
        if function_name == "get_closest_hospital":
            result = execute_tool(function_name, arguments)
            # Ensure result is a string
            if not isinstance(result, str):
                result = pyjson.dumps(result)
            chat_history.append({
                "role": "user",
                "content": f"this is the result of the function call: {result}, please continue the conversation"
            })
            ai_response = chat(chat_history)
            chat_history.append({"role": "assistant", "content": ai_response.content})
            sessions[session_id] = chat_history
            save_chat_sessions(sessions)
            resp = make_response(jsonify({"reply": ai_response.content}), 200)
            resp.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
            return resp
    
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Page not found"}), 404
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({"error": "No session found"}), 400
    
    sessions = load_chat_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_chat_sessions(sessions)
    
    resp = make_response(jsonify({"message": "Chat cleared"}), 200)
    resp.set_cookie('session_id', '', expires=0, httponly=True, samesite='Lax')
    return resp

# .well-known/appspecific/com.chrome.devtools.json    # 
@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def devtools_json():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'com.chrome.devtools.json')

if __name__ == '__main__':
    app.run(debug=True, port=5430)
