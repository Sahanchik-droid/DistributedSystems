# Microservices Project

## Services
- **Facade Service** (port 5000): Receives client requests, communicates with other services
- **Logging Service** (port 5001/gRPC 50051): Stores messages with deduplication
- **Messages Service** (port 5002): Returns static content

## Commands

```
# Setup
pip install -r requirements.txt
python generate_grpc.py

# Run Services (in separate terminals)
# Messages Service
cd messages_service
python app.py

# Logging Service
cd logging_service
python app.py  # HTTP version
# OR
python grpc_server.py  # gRPC version

# Facade Service
cd facade_service
python app.py  # HTTP only
# OR
python app_with_grpc.py  # With gRPC

# Test
curl -X POST -d "msg=Hello World" http://localhost:5000/message
curl http://localhost:5000/messages
```
