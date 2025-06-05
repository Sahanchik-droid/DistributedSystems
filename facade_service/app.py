from flask import Flask, request, jsonify
import requests
import uuid
import time
import sys
import os
import argparse
import random
from kafka import KafkaProducer

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import get_service_addresses
global kafka_producer
app = Flask(__name__)

MESSAGES_SERVICE_URL = "http://localhost:5002"
MAX_RETRIES = 3
config_server_url = "http://localhost:5003"  # Default, will be updated from command line

# Kafka producer will be initialized in main
kafka_producer = None
kafka_topic = "messages"

def get_service_url(service_name):
    """Get a random service URL from available instances"""
    addresses = get_service_addresses(service_name, config_server_url)
    if not addresses:
        if service_name == "logging-service":
            return "http://localhost:5001"  # Default fallback
        elif service_name == "messages-service":
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
    full_message = f"{message_id}:{message}"
    try:
        # Send message to Kafka
        kafka_producer.send(kafka_topic, value=full_message.encode('utf-8'))
        kafka_producer.flush()
        print(f"Sent message to Kafka: {full_message}")
    except Exception as e:
        print(f"Error sending to Kafka: {e}")
        return jsonify({"error": "Failed to send message to queue"}), 500

    # Also log to logging-service as before
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Get logging service URL dynamically
            logging_service_url = get_service_url("logging-service")
            
            response = requests.post(
                f"{logging_service_url}/log",
                json={"id": message_id, "message": message},
                timeout=5
            )
            if response.status_code == 200:
                return jsonify({"message": "Message logged and queued successfully", "id": message_id})
            retries += 1
            time.sleep(1)  # Add delay between retries
        except requests.exceptions.RequestException:
            retries += 1
            time.sleep(1)
    
    return jsonify({"error": "Failed to log message after retries"}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        # Get logging service URL dynamically
        logging_service_url = get_service_url("logging-service")
        
        logging_response = requests.get(f"{logging_service_url}/logs", timeout=5)
        logging_data = logging_response.text if logging_response.status_code == 200 else "Error fetching logs"
    except requests.exceptions.RequestException:
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
    parser = argparse.ArgumentParser(description='Facade Service (HTTP)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--config-server', type=str, default="http://localhost:5003", 
                       help='URL of the config server')
    parser.add_argument('--kafka-bootstrap-servers', type=str, default="localhost:9092,localhost:9093,localhost:9094",
                        help='Kafka bootstrap servers')
    args = parser.parse_args()
    
    # Set global config server URL
    config_server_url = args.config_server

    # Initialize Kafka producer
    kafka_producer = KafkaProducer(
        bootstrap_servers=args.kafka_bootstrap_servers.split(','),
        retries=5
    )
    
    app.run(host='0.0.0.0', port=args.port)
