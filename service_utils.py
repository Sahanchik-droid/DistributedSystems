import requests
import socket
import json
import os
import consul
import time
import psutil
import netifaces

def get_host_address():
    """Get the host's IP address that can be reached by other services"""
    try:
        # Try to get a proper network interface IP instead of loopback
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            # Skip loopback
            if interface.startswith('lo'):
                continue
            
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for address in addresses[netifaces.AF_INET]:
                    ip = address['addr']
                    # Skip local and special addresses
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        print(f"Using interface {interface} with IP {ip}")
                        return ip
    
        # Fallback to hostname method
        host_name = socket.gethostname()
        ip = socket.gethostbyname(host_name)
        print(f"Using hostname resolution: {host_name} -> {ip}")
        return ip
    except Exception as e:
        print(f"Error getting host address: {e}")
        # Return a safe value that should work for local services
        return "127.0.0.1"

def register_service(service_name, port, consul_host="localhost", consul_port=8500):
    """Register this service with Consul"""
    host_address = get_host_address()
    
    try:
        c = consul.Consul(host=consul_host, port=consul_port)
        
        # Register service with health check
        service_id = f"{service_name}-{host_address}-{port}"
        
        # Register with HTTP check
        check = consul.Check.http(
            f"http://{host_address}:{port}/health", 
            interval="10s", 
            timeout="5s"
        )
        
        c.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=host_address,
            port=port,
            check=check
        )
        
        print(f"Successfully registered {service_name} at {host_address}:{port}")
        return True
    
    except Exception as e:
        print(f"Error registering service with Consul: {e}")
        return False

def get_service_addresses(service_name, consul_host="localhost", consul_port=8500):
    """Get addresses for a given service from Consul"""
    try:
        c = consul.Consul(host=consul_host, port=consul_port)
        _, services = c.catalog.service(service_name)
        
        addresses = []
        for service in services:
            addresses.append(f"{service['ServiceAddress']}:{service['ServicePort']}")
        
        return addresses
    
    except Exception as e:
        print(f"Error getting service addresses from Consul: {e}")
        return []

def get_config_value(key, consul_host="localhost", consul_port=8500):
    """Get a configuration value from Consul KV store"""
    try:
        c = consul.Consul(host=consul_host, port=consul_port)
        index, data = c.kv.get(key)
        
        if data and data['Value']:
            return data['Value'].decode('utf-8')
        else:
            print(f"Config key {key} not found")
            return None
            
    except Exception as e:
        print(f"Error getting config from Consul: {e}")
        return None

def put_config_value(key, value, consul_host="localhost", consul_port=8500):
    """Put a configuration value into Consul KV store"""
    try:
        c = consul.Consul(host=consul_host, port=consul_port)
        c.kv.put(key, value)
        return True
    except Exception as e:
        print(f"Error putting config to Consul: {e}")
        return False
