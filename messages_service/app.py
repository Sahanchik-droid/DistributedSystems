from flask import Flask
import argparse
import sys
import os
import threading
from kafka import KafkaConsumer

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import register_service

app = Flask(__name__)

messages = []

def consume_messages(kafka_bootstrap_servers, group_id):
    consumer = KafkaConsumer(
        'messages',
        bootstrap_servers=kafka_bootstrap_servers,
        group_id=group_id,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda m: m.decode('utf-8')
    )
    print(f"[messages-service:{group_id}] Kafka consumer started")
    for msg in consumer:
        messages.append(msg.value)
        print(f"[messages-service:{group_id}] Received message: {msg.value}")

@app.route('/message', methods=['GET'])
def get_message():
    # Return all messages stored in this instance
    return "\n".join(messages)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Messages Service')
    parser.add_argument('--port', type=int, default=5002, help='Port to listen on')
    parser.add_argument('--config-server', type=str, default="http://localhost:5003", 
                       help='URL of the config server')
    parser.add_argument('--kafka-bootstrap-servers', type=str, default="localhost:9092,localhost:9093,localhost:9094",
                        help='Kafka bootstrap servers')
    parser.add_argument('--group-id', type=str, default=None, help='Kafka consumer group id (unique per instance)')
    args = parser.parse_args()
    
    # Register with config server
    register_service("messages-service", args.port, args.config_server)
    
    # Start Kafka consumer in background thread
    group_id = args.group_id or f"messages-service-{args.port}"
    consumer_thread = threading.Thread(
        target=consume_messages,
        args=(args.kafka_bootstrap_servers.split(','), group_id),
        daemon=True
    )
    consumer_thread.start()
    
    app.run(host='0.0.0.0', port=args.port)
