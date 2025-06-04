from flask import Flask, request, jsonify
import argparse
import json
import os

app = Flask(__name__)

# Default empty registry
services_registry = {
    "logging-service": [],
    "messages-service": []
}

CONFIG_FILE = "services_config.json"

def load_config_file():
    """Load service registry from config file if it exists"""
    global services_registry
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                services_registry = json.load(f)
            print(f"Loaded configuration from {CONFIG_FILE}")
        except Exception as e:
            print(f"Error loading config file: {e}")

@app.route('/register', methods=['POST'])
def register_service():
    """Register a service instance"""
    data = request.json
    service_name = data.get('name')
    service_address = data.get('address')
    
    if not service_name or not service_address:
        return jsonify({"error": "Service name and address are required"}), 400
    
    if service_name not in services_registry:
        services_registry[service_name] = []
    
    # Add address if not already registered
    if service_address not in services_registry[service_name]:
        services_registry[service_name].append(service_address)
        print(f"Registered {service_name} at {service_address}")
    
    return jsonify({
        "status": "registered",
        "name": service_name,
        "address": service_address
    })

@app.route('/services/<service_name>', methods=['GET'])
def get_service(service_name):
    """Get all addresses for a given service"""
    if service_name not in services_registry:
        return jsonify({"error": f"Service {service_name} not found"}), 404
    
    return jsonify({
        "name": service_name,
        "addresses": services_registry[service_name]
    })

@app.route('/services', methods=['GET'])
def get_all_services():
    """Get entire service registry"""
    return jsonify(services_registry)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Config Server')
    parser.add_argument('--port', type=int, default=5003, help='Port to listen on')
    parser.add_argument('--services', type=str, help='Initial services in JSON format')
    args = parser.parse_args()
    
    # Load services from file first
    load_config_file()
    
    # Override with command line if provided
    if args.services:
        try:
            cli_services = json.loads(args.services)
            services_registry.update(cli_services)
            print("Updated registry from command line arguments")
        except json.JSONDecodeError:
            print("Error parsing services JSON from command line")
    
    print(f"Starting config server with services: {services_registry}")
    app.run(host='0.0.0.0', port=args.port)
