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

def post_message(server_url, message):
    """Post a new message to the master server"""
    logger.info(f"Posting message to {server_url}: {message}")
    try:
        start_time = time.time()
        response = requests.post(
            f"{server_url}/messages",
            json={"message": message}
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            logger.info(f"Message posted successfully in {elapsed:.2f} seconds")
            print(f"Message posted successfully in {elapsed:.2f} seconds")
            return True
        else:
            logger.error(f"Failed to post message: {response.status_code} {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting message: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Client for Replicated Log System')
    parser.add_argument('--master', default='http://localhost:5000', help='Master server URL')
    parser.add_argument('--secondary', default=None, help='Secondary server URL (optional)')
    args = parser.parse_args()
    
    master_url = args.master
    secondary_url = args.secondary
    
    while True:
        print("\n=== Replicated Log Client ===")
        print("1. Post a message to the master")
        print("2. Get messages from the master")
        if secondary_url:
            print("3. Get messages from the secondary")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            message = input("Enter your message: ")
            post_message(master_url, message)
            
        elif choice == '2':
            get_messages(master_url)
            
        elif choice == '3' and secondary_url:
            get_messages(secondary_url)
            
        elif choice == '4':
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
