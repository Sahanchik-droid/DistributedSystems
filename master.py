from flask import Flask, request, jsonify
import requests
import logging
import os
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Master")

app = Flask(__name__)

# In-memory list to store messages
messages = []

# Get secondary server addresses from environment variables
# Format: SECONDARIES=http://secondary1:5001,http://secondary2:5001,...
secondaries_str = os.environ.get("SECONDARIES", "")
SECONDARY_SERVERS = secondaries_str.split(",") if secondaries_str else []

logger.info(f"Master starting with secondaries: {SECONDARY_SERVERS}")

@app.route('/messages', methods=['GET'])
def get_messages():
    """Return all messages in the log"""
    logger.info(f"GET request received. Returning {len(messages)} messages.")
    return jsonify(messages)

@app.route('/messages', methods=['POST'])
def post_message():
    """Append a message to the log and replicate to all secondaries"""
    message = request.json.get('message')
    if not message:
        logger.warning("POST request received without message")
        return jsonify({"error": "No message provided"}), 400
    
    # Add message to local log
    messages.append(message)
    logger.info(f"Added message to log: {message}")
    
    # If no secondaries, return immediately
    if not SECONDARY_SERVERS:
        logger.info("No secondaries to replicate to. Returning.")
        return jsonify({"status": "success", "message": "Message added to log"})
        
    # Replicate to all secondaries and wait for ACKs
    for secondary in SECONDARY_SERVERS:
        if not secondary:  # Skip empty entries
            continue
            
        try:
            logger.info(f"Replicating message to {secondary}")
            response = requests.post(
                f"{secondary}/replicate",
                json={"message": message},
                timeout=60  # Long timeout to handle secondary delays
            )
            
            if response.status_code == 200:
                logger.info(f"Received ACK from {secondary}")
            else:
                logger.error(f"Failed to replicate to {secondary}: {response.status_code} {response.text}")
                return jsonify({
                    "error": f"Replication failed for secondary {secondary}"
                }), 500
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while replicating to {secondary}: {str(e)}")
            return jsonify({
                "error": f"Replication failed for secondary {secondary}: {str(e)}"
            }), 500

    return jsonify({
        "status": "success", 
        "message": "Message added to log and replicated to all secondaries"
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
