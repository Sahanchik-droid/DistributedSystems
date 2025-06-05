import grpc
import sys
import os
import random
import time

# Add parent directory to path to find generated module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import messages_pb2, messages_pb2_grpc
from service_utils import get_service_addresses

def get_logging_services(consul_host="localhost", consul_port=8500):
    """Get available logging service addresses from Consul"""
    addresses = get_service_addresses("logging-service", consul_host, consul_port)
    if not addresses:
        print("Warning: No logging services found, using default fallback")
        return ['localhost:50051']  # Fallback to default
    return addresses

def log_message(message_id, message, consul_host="localhost", consul_port=8500):
    # Get available logging services dynamically
    available_services = get_logging_services(consul_host, consul_port)
    services_to_try = available_services.copy()
    
    while services_to_try:
        # Select a random service
        service = random.choice(services_to_try)
        services_to_try.remove(service)
        
        try:
            with grpc.insecure_channel(service) as channel:
                stub = messages_pb2_grpc.LoggingServiceStub(channel)
                response = stub.LogMessage(
                    messages_pb2.LogRequest(id=message_id, message=message),
                    timeout=3  # Set timeout for quicker failover
                )
                print(f"Successfully connected to {service}")
                return response.success, response.message
        except grpc.RpcError as e:
            print(f"Service {service} unavailable: {e}")
            continue
    
    # If all services failed
    return False, "All logging services are unavailable"

def get_logs(consul_host="localhost", consul_port=8500):
    # Get available logging services dynamically
    available_services = get_logging_services(consul_host, consul_port)
    services_to_try = available_services.copy()
    
    while services_to_try:
        # Select a random service
        service = random.choice(services_to_try)
        services_to_try.remove(service)
        
        try:
            with grpc.insecure_channel(service) as channel:
                stub = messages_pb2_grpc.LoggingServiceStub(channel)
                response = stub.GetLogs(
                    messages_pb2.GetLogsRequest(),
                    timeout=3  # Set timeout for quicker failover
                )
                print(f"Successfully connected to {service}")
                return response.messages
        except grpc.RpcError as e:
            print(f"Service {service} unavailable: {e}")
            continue
    
    # If all services failed
    return ["All logging services are unavailable"]
