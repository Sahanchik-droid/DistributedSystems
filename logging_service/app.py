from flask import Flask, request, jsonify
import hazelcast
import argparse
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import register_service, get_config_value

app = Flask(__name__)

# Initialize Hazelcast client
hazelcast_config = None
client = None
logs_map = None

def init_hazelcast(consul_host, consul_port):
    global client, logs_map
    
    # Get Hazelcast configuration from Consul
    hazelcast_config_str = get_config_value('config/hazelcast', consul_host, consul_port)
    
    if hazelcast_config_str:
        try:
            hazelcast_config = json.loads(hazelcast_config_str)
            print(f"Using Hazelcast config from Consul: {hazelcast_config}")
            
            # Create client with the retrieved configuration
            client = hazelcast.HazelcastClient(
                cluster_members=hazelcast_config.get('cluster_members', ['localhost:5701']),
                cluster_name=hazelcast_config.get('cluster_name', 'dev')
            )
        except Exception as e:
            print(f"Error parsing Hazelcast config: {e}")
            client = hazelcast.HazelcastClient()  # Use default config as fallback
    else:
        # Use default config if not found in Consul
        client = hazelcast.HazelcastClient()
        
    logs_map = client.get_map("logs").blocking()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

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
    parser.add_argument('--consul-host', type=str, default="localhost", 
                       help='Consul host')
    parser.add_argument('--consul-port', type=int, default=8500,
                       help='Consul port')
    args = parser.parse_args()
    
    # Initialize Hazelcast from consul config
    init_hazelcast(args.consul_host, args.consul_port)
    
    # Register with Consul
    register_service("logging-service", args.port, args.consul_host, args.consul_port)
    
    print("Connected to Hazelcast cluster")
    app.run(host='0.0.0.0', port=args.port)
