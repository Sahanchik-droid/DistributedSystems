import requests
import json
import logging
import sys
import time
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Client")

def get_messages(server_url):
    """Retrieve all messages from the specified server"""
    logger.info(f"Retrieving messages from {server_url}")
    try:
        start_time = time.time()
        response = requests.get(f"{server_url}/messages")
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"Retrieved {len(messages)} messages in {elapsed:.2f} seconds")
            print("\n=== Messages ===")
            for i, msg in enumerate(messages, 1):
                print(f"{i}. {msg}")
            return messages
        else:
            logger.error(f"Failed to retrieve messages: {response.status_code} {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        return None

def post_message(server_url, message, write_concern=None):
    """Post a new message to the master server with optional write concern"""
    payload = {"message": message}
    
    # Add write concern parameter if specified
    if write_concern is not None:
        payload["w"] = write_concern
        logger.info(f"Posting message to {server_url} with write concern w={write_concern}: {message}")
    else:
        logger.info(f"Posting message to {server_url}: {message}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{server_url}/messages",
            json=payload
        )
        elapsed = time.time() - start_time
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Message posted successfully in {elapsed:.2f} seconds")
            print(f"Message posted successfully in {elapsed:.2f} seconds")
            if response.status_code == 202:
                print("Note: Message was added with partial replication (not all ACKs received)")
            print(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"Failed to post message: {response.status_code} {response.text}")
            print(f"Error: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting message: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Client for Replicated Log System')
    parser.add_argument('--master', default='http://localhost:5000', help='Master server URL')
    parser.add_argument('--secondary1', default='http://localhost:5001', help='First Secondary server URL')
    parser.add_argument('--secondary2', default='http://localhost:5002', help='Second Secondary server URL')
    args = parser.parse_args()
    
    master_url = args.master
    secondary1_url = args.secondary1
    secondary2_url = args.secondary2
    
    while True:
        print("\n=== Replicated Log Client ===")
        print("1. Post a message to the master (all ACKs)")
        print("2. Post a message with write concern w=1 (master only)")
        print("3. Post a message with write concern w=2 (master + 1 secondary)")
        print("4. Post a message with write concern w=3 (master + 2 secondaries)")
        print("5. Get messages from the master")
        print("6. Get messages from secondary 1")
        print("7. Get messages from secondary 2")
        print("8. Compare all nodes (check consistency)")
        print("9. Exit")
        
        choice = input("Enter your choice (1-9): ")
        
        if choice == '1':
            message = input("Enter your message: ")
            post_message(master_url, message)
            
        elif choice == '2':
            message = input("Enter your message: ")
            post_message(master_url, message, write_concern=1)
            
        elif choice == '3':
            message = input("Enter your message: ")
            post_message(master_url, message, write_concern=2)
            
        elif choice == '4':
            message = input("Enter your message: ")
            post_message(master_url, message, write_concern=3)
            
        elif choice == '5':
            get_messages(master_url)
            
        elif choice == '6':
            get_messages(secondary1_url)
            
        elif choice == '7':
            get_messages(secondary2_url)
            
        elif choice == '8':
            print("\nComparing all nodes for consistency...\n")
            master_msgs = get_messages(master_url)
            sec1_msgs = get_messages(secondary1_url)
            sec2_msgs = get_messages(secondary2_url)
            
            print("\nConsistency Report:")
            master_count = len(master_msgs) if master_msgs else 0
            sec1_count = len(sec1_msgs) if sec1_msgs else 0
            sec2_count = len(sec2_msgs) if sec2_msgs else 0
            
            print(f"Master: {master_count} messages")
            print(f"Secondary 1: {sec1_count} messages")
            print(f"Secondary 2: {sec2_count} messages")
            
            if master_count == sec1_count == sec2_count:
                print("All nodes are consistent!")
            else:
                print("Nodes are inconsistent - eventual consistency in progress")
            
        elif choice == '9':
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
