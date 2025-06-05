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

## Kafka Setup

- Kafka cluster is defined in `docker-compose.yml` (3 brokers).
- Start with:  
  ```
  docker-compose up -d
  ```

## Running Multiple Instances

- Run multiple `messages-service` instances on different ports and with unique `--group-id` (or default).
- Run multiple `logging-service` instances on different ports.

## Example Commands

```bash
# Start Kafka cluster
docker-compose up -d

# Run two messages-service instances
cd messages_service
python app.py --port 5002 --group-id ms1
python app.py --port 5004 --group-id ms2

# Run three logging-service instances
cd logging_service
python app.py --port 5001
python app.py --port 5005
python app.py --port 5006

# Run facade-service
cd facade_service
python app.py --kafka-bootstrap-servers localhost:9092,localhost:9093,localhost:9094

# Send messages
for i in {1..10}; do curl -X POST -d "msg=msg$i" http://localhost:5000/message; done

# Check logs in each logging-service and messages-service terminal

# Get combined messages (repeat several times)
curl http://localhost:5000/messages
```
