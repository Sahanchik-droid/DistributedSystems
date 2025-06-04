import grpc
from concurrent import futures
import sys
import os
import hazelcast
import argparse

# Add parent directory to path to find generated module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import messages_pb2, messages_pb2_grpc
from service_utils import register_service

# Initialize Hazelcast client
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

def serve(port=50051, config_server_url="http://localhost:5003"):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingServicer(), server)
    server_address = f'[::]:{port}'
    server.add_insecure_port(server_address)
    server.start()
    print(f"gRPC server started on port {port}")
    print("Connected to Hazelcast cluster")
    
    # Register with config server
    register_service("logging-service", port, config_server_url)
    
    server.wait_for_termination()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='gRPC Logging Service')
    parser.add_argument('--port', type=int, default=50051, help='Port to listen on')
    parser.add_argument('--config-server', type=str, default="http://localhost:5003", 
                       help='URL of the config server')
    args = parser.parse_args()
    
    serve(args.port, args.config_server)
