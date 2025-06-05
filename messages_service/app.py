from flask import Flask, jsonify
import argparse
import sys
import os
import threading
import json
from kafka import KafkaConsumer

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import register_service, get_config_value

app = Flask(__name__)

messages = []

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

def consume_messages(kafka_config, group_id):
    consumer = KafkaConsumer(
        kafka_config.get("topic", "messages"),
        bootstrap_servers=kafka_config.get("bootstrap_servers", "localhost:9092").split(','),
        group_id=group_id,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda m: m.decode('utf-8')
    )
    print(f"[messages-service:{group_id}] Kafka consumer started")
    for msg in consumer:
        messages.append(msg.value)
        print(f"[messages-service:{group_id}] Received message: {msg.value}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/message', methods=['GET'])
def get_message():
    # Return all messages stored in this instance
    return "\n".join(messages)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Messages Service')
    parser.add_argument('--port', type=int, default=5002, help='Port to listen on')
    parser.add_argument('--consul-host', type=str, default="localhost", 
                       help='Consul host')
    parser.add_argument('--consul-port', type=int, default=8500,
                       help='Consul port')
    parser.add_argument('--group-id', type=str, default=None, help='Kafka consumer group id (unique per instance)')
    args = parser.parse_args()
    
    # Register with Consul
    register_service("messages-service", args.port, args.consul_host, args.consul_port)
    
    # Get Kafka configuration from Consul
    kafka_config = get_kafka_config(args.consul_host, args.consul_port)
    
    # Start Kafka consumer in background thread
    group_id = args.group_id or f"messages-service-{args.port}"
    consumer_thread = threading.Thread(
        target=consume_messages,
        args=(kafka_config, group_id),
        daemon=True
    )
    consumer_thread.start()
    
    app.run(host='0.0.0.0', port=args.port)
