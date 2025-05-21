from flask import Flask, request, jsonify
import requests
import uuid
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facade_service.grpc_client import log_message, get_logs

app = Flask(__name__)

MESSAGES_SERVICE_URL = "http://localhost:5002"
MAX_RETRIES = 3

@app.route('/message', methods=['POST'])
def post_message():
    message = request.form.get('msg')
    if not message:
        return jsonify({"error": "msg parameter is required"}), 400
    
    message_id = str(uuid.uuid4())
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            success, response_message = log_message(message_id, message)
            if success:
                return jsonify({"message": "Message logged successfully", "id": message_id})
            retries += 1
            time.sleep(1)  # Add delay between retries
        except Exception as e:
            print(f"Error: {e}")
            retries += 1
            time.sleep(1)
    
    return jsonify({"error": "Failed to log message after retries"}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        logging_data = "\n".join(get_logs())
    except Exception as e:
        print(f"Error getting logs: {e}")
        logging_data = "Logging service unavailable"
    
    try:
        messages_response = requests.get(f"{MESSAGES_SERVICE_URL}/message", timeout=5)
        messages_data = messages_response.text if messages_response.status_code == 200 else "Error fetching messages"
    except requests.exceptions.RequestException:
        messages_data = "Messages service unavailable"
    
    return f"{logging_data}\n{messages_data}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
