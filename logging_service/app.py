from flask import Flask, request, jsonify
from concurrent import futures
import grpc
import threading
import sys
import os

app = Flask(__name__)

logs = {}

@app.route('/log', methods=['POST'])
def log_message():
    data = request.json
    message_id = data.get('id')
    message = data.get('message')
    
    if not message_id or not message:
        return jsonify({"error": "id and message are required"}), 400
    
    if message_id not in logs:
        logs[message_id] = message
        print(f"Logged: {message_id} - {message}")
    else:
        print(f"Duplicate message ignored: {message_id}")
    
    return jsonify({"message": "Logged successfully"})

@app.route('/logs', methods=['GET'])
def get_logs():
    return "\n".join(logs.values())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
