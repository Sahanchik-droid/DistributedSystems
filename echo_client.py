import socket
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EchoClient")

def start_client(host='localhost', port=8888):
    """Start a client to connect to the echo server."""
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect the socket to the server
    server_address = (host, port)
    logger.info(f"Connecting to {host}:{port}...")
    
    try:
        client_socket.connect(server_address)
        logger.info("Connection established!")
        
        while True:
            # Get input message from user
            message = input("Enter message (or 'quit' to exit): ")
            
            if message.lower() == 'quit':
                break
            
            # Send the message
            client_socket.sendall(message.encode('utf-8'))
            logger.info(f"Sent: {message}")
            
            # Receive the response
            data = client_socket.recv(1024)
            response = data.decode('utf-8')
            logger.info(f"Received: {response}")
    
    except ConnectionRefusedError:
        logger.error("Connection refused. Make sure the server is running.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up the connection
        client_socket.close()
        logger.info("Connection closed")

if __name__ == "__main__":
    start_client()
