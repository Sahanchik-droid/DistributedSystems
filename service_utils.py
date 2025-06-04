import requests
import socket

def get_host_address():
    """Get the host's IP address"""
    # This gets the host's name and tries to resolve it to an IP address
    # For local testing, this will often be 127.0.0.1
    host_name = socket.gethostname()
    return socket.gethostbyname(host_name)

def register_service(service_name, port, config_server_url="http://localhost:5003"):
    """Register this service with the config server"""
    host_address = get_host_address()
    service_address = f"{host_address}:{port}"
    
    try:
        response = requests.post(
            f"{config_server_url}/register",
            json={
                "name": service_name,
                "address": service_address
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"Successfully registered {service_name} at {service_address}")
            return True
        else:
            print(f"Failed to register service: {response.text}")
            return False
    
    except requests.RequestException as e:
        print(f"Error registering service: {e}")
        return False

def get_service_addresses(service_name, config_server_url="http://localhost:5003"):
    """Get addresses for a given service from config server"""
    try:
        response = requests.get(
            f"{config_server_url}/services/{service_name}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("addresses", [])
        else:
            print(f"Failed to get service addresses: {response.text}")
            return []
    
    except requests.RequestException as e:
        print(f"Error getting service addresses: {e}")
        return []
