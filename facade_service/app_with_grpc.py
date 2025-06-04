from flask import Flask, request, jsonify
import requests
import uuid
import time
import sys
import os
import argparse
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facade_service.grpc_client import log_message, get_logs
from service_utils import get_service_addresses

app = Flask(__name__)

MAX_RETRIES = 3
config_server_url = "http://localhost:5003"  # Default, will be updated from command line

def get_service_url(service_name):
    """Get a random service URL from available instances"""
    addresses = get_service_addresses(service_name, config_server_url)
    if not addresses:
        if service_name == "messages-service":
            return "http://localhost:5002"  # Default fallback
        return None
        
    # Select random address and ensure it has http:// prefix
    address = random.choice(addresses)
    if not address.startswith("http://"):
        address = f"http://{address}"
    return address

@app.route('/message', methods=['POST'])
def post_message():
    message = request.form.get('msg')
    if not message:
        return jsonify({"error": "msg parameter is required"}), 400
    
    message_id = str(uuid.uuid4())
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            success, response_message = log_message(message_id, message, config_server_url)
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
        logging_data = "\n".join(get_logs(config_server_url))
    except Exception as e:
        print(f"Error getting logs: {e}")
        logging_data = "Logging service unavailable"
    
    try:
        # Get messages service URL dynamically
        messages_service_url = get_service_url("messages-service")
        
        messages_response = requests.get(f"{messages_service_url}/message", timeout=5)
        messages_data = messages_response.text if messages_response.status_code == 200 else "Error fetching messages"
    except requests.exceptions.RequestException:
        messages_data = "Messages service unavailable"
    
    return f"{logging_data}\n{messages_data}"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facade Service (gRPC)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--config-server', type=str, default="http://localhost:5003", 
                       help='URL of the config server')
    args = parser.parse_args()
    
    # Set global config server URL
    config_server_url = args.config_server
    
    app.run(host='0.0.0.0', port=args.port)
