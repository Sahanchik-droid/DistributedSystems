from flask import Flask, request, jsonify
import requests
import os
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory storage for messages
messages = []
is_master = os.environ.get('IS_MASTER', 'false').lower() == 'true'
master_url = os.environ.get('MASTER_URL', 'http://localhost:5000')
secondary_urls = os.environ.get('SECONDARY_URLS', '').split(',') if os.environ.get('SECONDARY_URLS') else []
# Filter out empty strings
secondary_urls = [url for url in secondary_urls if url]

# Add artificial delay for secondaries (in seconds)
SECONDARY_DELAY = 8

# Add lock for thread safety
message_lock = threading.Lock()

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages)

@app.route('/messages', methods=['POST'])
def add_message():
    if not is_master:
        return jsonify({"error": "Only master node can accept write requests"}), 400
    
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    # Get write concern parameter (default to all nodes if not specified)
    write_concern = int(data.get('w', len(secondary_urls) + 1))
    
    # Validate write concern
    if write_concern < 1 or write_concern > len(secondary_urls) + 1:
        return jsonify({"error": f"Invalid write concern. Must be between 1 and {len(secondary_urls) + 1}"}), 400
    
    # Create message with unique ID and timestamp
    msg = {
        "id": str(uuid.uuid4()),
        "message": data['message'],
        "timestamp": datetime.now().isoformat()
    }
    
    # First, add to master
    with message_lock:
        # Check for duplicates (by message content)
        if not any(existing['message'] == msg['message'] for existing in messages):
            messages.append(msg)
        else:
            return jsonify({"error": "Duplicate message"}), 400
    
    # Always replicate to secondaries, regardless of write concern
    ack_events = []
    
    for url in secondary_urls:
        event = threading.Event()
        ack_events.append(event)
        threading.Thread(target=replicate_to_secondary, args=(url, msg, event)).start()
    
    # If write concern is 1 (master only), return immediately without waiting for ACKs
    if write_concern == 1:
        return jsonify({
            "status": "Message added successfully",
            "message": msg,
            "replication": "async"
        }), 201
    
    # Otherwise, wait for required number of ACKs
    ack_count = 1  # Master counts as 1
    for event in ack_events[:write_concern-1]:
        if event.wait(timeout=5):  # 5 seconds timeout
            ack_count += 1
        else:
            break  # Stop waiting if timeout occurs
    
    if ack_count >= write_concern:
        return jsonify({
            "status": "Message added successfully",
            "message": msg,
            "acks": ack_count
        }), 201
    else:
        # Still return success if master has it, but indicate partial replication
        return jsonify({
            "status": "Message added with partial replication",
            "message": msg,
            "acks": ack_count,
            "requested_acks": write_concern
        }), 202

def replicate_to_secondary(url, message, ack_event):
    try:
        response = requests.post(f"{url}/replicate", json=message)
        if response.status_code == 200:
            ack_event.set()  # Signal that ACK was received
    except:
        pass  # Ignore connection errors - handled by timeout in the main thread

@app.route('/replicate', methods=['POST'])
def replicate():
    if is_master:
        return jsonify({"error": "Master node cannot accept replication requests"}), 400
    
    message = request.json
    
    # Simulate network delay
    time.sleep(SECONDARY_DELAY)
    
    with message_lock:
        # Check for duplicate by ID
        if not any(existing['id'] == message['id'] for existing in messages):
            messages.append(message)
    
    return jsonify({"status": "Message replicated successfully"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    role = "Master" if is_master else "Secondary"
    return jsonify({
        "status": "healthy",
        "role": role,
        "message_count": len(messages)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
