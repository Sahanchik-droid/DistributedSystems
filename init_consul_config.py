import argparse
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import put_config_value

def main():
    parser = argparse.ArgumentParser(description='Initialize Consul Configuration')
    parser.add_argument('--consul-host', type=str, default="localhost", help='Consul host')
    parser.add_argument('--consul-port', type=int, default=8500, help='Consul port')
    args = parser.parse_args()
    
    # Kafka configuration
    kafka_config = {
        "bootstrap_servers": "localhost:9092,localhost:9093,localhost:9094",
        "topic": "messages"
    }
    
    # Hazelcast configuration
    hazelcast_config = {
        "cluster_members": ["localhost:5701"],
        "cluster_name": "dev"
    }
    
    # Store configurations
    put_config_value('config/kafka', json.dumps(kafka_config), args.consul_host, args.consul_port)
    put_config_value('config/hazelcast', json.dumps(hazelcast_config), args.consul_host, args.consul_port)
    
    print("Consul configuration initialized successfully!")

if __name__ == '__main__':
    main()
