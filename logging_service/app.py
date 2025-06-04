from flask import Flask, request, jsonify
import hazelcast
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import register_service

app = Flask(__name__)

# Initialize Hazelcast client
client = hazelcast.HazelcastClient()
logs_map = client.get_map("logs").blocking()

@app.route('/log', methods=['POST'])
def log_message():
    data = request.json
    message_id = data.get('id')
    message = data.get('message')
    
    if not message_id or not message:
        return jsonify({"error": "id and message are required"}), 400
    
    if not logs_map.contains_key(message_id):
        logs_map.put(message_id, message)
        print(f"Logged: {message_id} - {message}")
    else:
        print(f"Duplicate message ignored: {message_id}")
    
    return jsonify({"message": "Logged successfully"})

@app.route('/logs', methods=['GET'])
def get_logs():
    values = logs_map.values()
    return "\n".join(values)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Logging Service')
    parser.add_argument('--port', type=int, default=5001, help='Port to listen on')
    parser.add_argument('--config-server', type=str, default="http://localhost:5003", 
                       help='URL of the config server')
    args = parser.parse_args()
    
    # Register with config server
    register_service("logging-service", args.port, args.config_server)
    
    print("Connected to Hazelcast cluster")
    app.run(host='0.0.0.0', port=args.port)
