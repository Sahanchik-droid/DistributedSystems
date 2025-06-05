from flask import Flask, request, jsonify
import requests
import uuid
import time
import sys
import os
import argparse
import random
import json
from kafka import KafkaProducer

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import get_service_addresses, get_config_value, register_service

app = Flask(__name__)

MAX_RETRIES = 3
kafka_producer = None

def get_kafka_config(consul_host, consul_port):
    """Get Kafka configuration from Consul KV store"""
    kafka_config_str = get_config_value('config/kafka', consul_host, consul_port)
    
    if kafka_config_str:
        try:
            return json.loads(kafka_config_str)
        except Exception as e:
            print(f"Error parsing Kafka config: {e}")
    
    # Default configuration if not found in Consul
    return {
        "bootstrap_servers": "localhost:9092,localhost:9093,localhost:9094",
        "topic": "messages"
    }

def get_service_url(service_name, consul_host, consul_port):
    """Get a random service URL from available instances"""
    addresses = get_service_addresses(service_name, consul_host, consul_port)
    if not addresses:
        if service_name == "logging-service":
            print(f"No {service_name} instances found in Consul, using default")
            return "http://localhost:5001"  # Default fallback
        elif service_name == "messages-service":
            print(f"No {service_name} instances found in Consul, using default")
            return "http://localhost:5002"  # Default fallback
        return None
    
    print(f"Found {len(addresses)} instances of {service_name}: {addresses}")
        
    # Select random address and ensure it has http:// prefix
    address = random.choice(addresses)
    if not address.startswith("http://"):
        address = f"http://{address}"
    print(f"Selected {service_name} instance: {address}")
    return address

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/message', methods=['POST'])
def post_message():
    message = request.form.get('msg')
    if not message:
        return jsonify({"error": "msg parameter is required"}), 400
    
    message_id = str(uuid.uuid4())
    full_message = f"{message_id}:{message}"
    
    # Get Kafka config from global object
    kafka_config = app.config['kafka_config']
    
    try:
        # Send message to Kafka
        kafka_producer.send(kafka_config.get("topic", "messages"), value=full_message.encode('utf-8'))
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
            logging_service_url = get_service_url("logging-service", 
                                                app.config['consul_host'], 
                                                app.config['consul_port'])
            
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
        logging_service_url = get_service_url("logging-service", 
                                             app.config['consul_host'], 
                                             app.config['consul_port'])
        
        logging_response = requests.get(f"{logging_service_url}/logs", timeout=5)
        logging_data = logging_response.text if logging_response.status_code == 200 else "Error fetching logs"
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to logging service: {e}")
        logging_data = "Logging service unavailable"
    
    try:
        # Get messages service URL dynamically
        messages_service_url = get_service_url("messages-service", 
                                              app.config['consul_host'], 
                                              app.config['consul_port'])
        
        messages_response = requests.get(f"{messages_service_url}/message", timeout=5)
        if messages_response.status_code == 200:
            messages_data = messages_response.text
            if messages_data:
                print(f"Successfully retrieved messages: {messages_data[:50]}...")
            else:
                print("Messages service returned empty response")
                messages_data = "No messages available"
        else:
            print(f"Error fetching messages: {messages_response.status_code}")
            messages_data = "Error fetching messages"
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to messages service: {e}")
        messages_data = "Messages service unavailable"
    
    return f"{logging_data}\n{messages_data}"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facade Service (HTTP)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--consul-host', type=str, default="localhost", 
                       help='Consul host')
    parser.add_argument('--consul-port', type=int, default=8500,
                       help='Consul port')
    args = parser.parse_args()
    
    # Register with Consul
    register_service("facade-service", args.port, args.consul_host, args.consul_port)
    
    # Store Consul connection details in app config
    app.config['consul_host'] = args.consul_host
    app.config['consul_port'] = args.consul_port
    
    # Get Kafka config from Consul
    kafka_config = get_kafka_config(args.consul_host, args.consul_port)
    app.config['kafka_config'] = kafka_config

    # Initialize Kafka producer with config from Consul
    kafka_producer = KafkaProducer(
        bootstrap_servers=kafka_config.get("bootstrap_servers", "localhost:9092").split(','),
        retries=5
    )
    
    app.run(host='0.0.0.0', port=args.port)
