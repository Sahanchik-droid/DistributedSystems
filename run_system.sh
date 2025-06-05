#!/bin/bash

# Start Consul in development mode in the background
echo "Starting Consul..."
consul agent -dev -ui -client=0.0.0.0 -data-dir=./consul_data > consul.log 2>&1 &

# Wait for Consul to initialize
echo "Waiting for Consul to initialize..."
sleep 5

# Initialize Consul with config values
echo "Initializing Consul configuration..."
python init_consul_config.py

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

# Wait for Kafka to initialize
echo "Waiting for Kafka to initialize..."
sleep 10

# Generate gRPC code
echo "Generating gRPC code..."
python generate_grpc.py

echo "System is ready!"
echo "You can now start services in separate terminals:"
echo "- python logging_service/app.py --port 5001"
echo "- python logging_service/grpc_server.py --port 50051"
echo "- python messages_service/app.py --port 5002 --group-id messages-1"
echo "- python facade_service/app.py --port 5000"

echo "Consul UI is available at: http://localhost:8500"
echo "Kafka UI is available at: http://localhost:8080"
