import grpc
import sys
import os

# Add parent directory to path to find generated module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import messages_pb2, messages_pb2_grpc

def log_message(message_id, message):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = messages_pb2_grpc.LoggingServiceStub(channel)
        response = stub.LogMessage(messages_pb2.LogRequest(id=message_id, message=message))
        return response.success, response.message

def get_logs():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = messages_pb2_grpc.LoggingServiceStub(channel)
        response = stub.GetLogs(messages_pb2.GetLogsRequest())
        return response.messages
