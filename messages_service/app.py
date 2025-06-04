from flask import Flask
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_utils import register_service

app = Flask(__name__)

@app.route('/message', methods=['GET'])
def get_message():
    return "not implemented yet"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Messages Service')
    parser.add_argument('--port', type=int, default=5002, help='Port to listen on')
    parser.add_argument('--config-server', type=str, default="http://localhost:5003", 
                       help='URL of the config server')
    args = parser.parse_args()
    
    # Register with config server
    register_service("messages-service", args.port, args.config_server)
    
    app.run(host='0.0.0.0', port=args.port)
