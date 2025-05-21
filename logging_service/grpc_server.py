import grpc
from concurrent import futures
import sys
import os

# Add parent directory to path to find generated module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import messages_pb2, messages_pb2_grpc

# In-memory storage for logs
logs = {}

class LoggingServicer(messages_pb2_grpc.LoggingServiceServicer):
    def LogMessage(self, request, context):
        message_id = request.id
        message = request.message
        
        # Deduplication check
        if message_id not in logs:
            logs[message_id] = message
            print(f"Logged via gRPC: {message_id} - {message}")
        else:
            print(f"Duplicate message ignored via gRPC: {message_id}")
        
        return messages_pb2.LogResponse(success=True, message="Logged successfully")
    
    def GetLogs(self, request, context):
        return messages_pb2.GetLogsResponse(messages=list(logs.values()))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
