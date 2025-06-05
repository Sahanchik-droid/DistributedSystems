import grpc
from concurrent import futures
import sys
import os
import hazelcast
import argparse
import json

# Add parent directory to path to find generated module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import messages_pb2, messages_pb2_grpc
from service_utils import register_service, get_config_value
from flask import Flask, jsonify
import threading

# Create a minimal Flask app for health checks
health_app = Flask(__name__)

@health_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

def run_health_server(port):
    health_app.run(host='0.0.0.0', port=port)

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

class LoggingServicer(messages_pb2_grpc.LoggingServiceServicer):
    def LogMessage(self, request, context):
        message_id = request.id
        message = request.message
        
        # Deduplication check using Hazelcast distributed map
        if not logs_map.contains_key(message_id):
            logs_map.put(message_id, message)
            print(f"Logged via gRPC: {message_id} - {message}")
        else:
            print(f"Duplicate message ignored via gRPC: {message_id}")
        
        return messages_pb2.LogResponse(success=True, message="Logged successfully")
    
    def GetLogs(self, request, context):
        # Get all values from the distributed map
        values = logs_map.values()
        return messages_pb2.GetLogsResponse(messages=list(values))

def serve(port=50051, consul_host="localhost", consul_port=8500):
    # Start health check server on a separate thread
    health_port = port + 100  # Use a different port for health checks
    health_thread = threading.Thread(target=run_health_server, args=(health_port,), daemon=True)
    health_thread.start()
    
    # Initialize Hazelcast
    init_hazelcast(consul_host, consul_port)
    
    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingServicer(), server)
    server_address = f'[::]:{port}'
    server.add_insecure_port(server_address)
    server.start()
    print(f"gRPC server started on port {port}")
    print("Connected to Hazelcast cluster")
    
    # Register with Consul
    register_service("logging-service", health_port, consul_host, consul_port)
    
    server.wait_for_termination()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='gRPC Logging Service')
    parser.add_argument('--port', type=int, default=50051, help='Port to listen on')
    parser.add_argument('--consul-host', type=str, default="localhost", 
                       help='Consul host')
    parser.add_argument('--consul-port', type=int, default=8500,
                       help='Consul port')
    args = parser.parse_args()
    
    serve(args.port, args.consul_host, args.consul_port)
