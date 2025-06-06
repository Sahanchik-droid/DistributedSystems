from flask import Flask, request, jsonify
import logging
import time
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Secondary")

app = Flask(__name__)

# In-memory list to store replicated messages
messages = []

# Get replication delay from environment variable (in seconds)
REPLICATION_DELAY = int(os.environ.get("REPLICATION_DELAY", "1"))

logger.info(f"Secondary starting with replication delay: {REPLICATION_DELAY} seconds")

@app.route('/messages', methods=['GET'])
def get_messages():
    """Return all replicated messages"""
    logger.info(f"GET request received. Returning {len(messages)} messages.")
    return jsonify(messages)

@app.route('/replicate', methods=['POST'])
def replicate():
    """Receive a message from master and store it after delay"""
    message = request.json.get('message')
    
    if not message:
        logger.warning("Replication request received without message")
        return jsonify({"error": "No message provided"}), 400
    
    # Simulate delay to test blocking replication
    logger.info(f"Received replication request. Delaying for {REPLICATION_DELAY} seconds...")
    time.sleep(REPLICATION_DELAY)
    
    # Store the message
    messages.append(message)
    logger.info(f"Added message to replicated log: {message}")
    
    # Send ACK back to master
    return jsonify({"status": "success", "message": "Message replicated successfully"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)
