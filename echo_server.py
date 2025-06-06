import socket
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EchoServer")

def start_server(host='0.0.0.0', port=8888):
    """Start the echo server on the specified host and port."""
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set socket option to reuse address
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind the socket to the address
    server_address = (host, port)
    server_socket.bind(server_address)
    
    # Listen for incoming connections (max 5 queued)
    server_socket.listen(5)
    
    logger.info(f"Server started on {host}:{port}")
    
    try:
        while True:
            # Wait for a connection
            logger.info("Waiting for a connection...")
            client_socket, client_address = server_socket.accept()
            
            try:
                logger.info(f"Connection established from {client_address}")
                
                # Receive and echo data
                while True:
                    data = client_socket.recv(1024)
                    if data:
                        # Echo back the received data
                        message = data.decode('utf-8').strip()
                        logger.info(f"Received: {message}")
                        
                        response = f"Echo: {message}"
                        client_socket.sendall(response.encode('utf-8'))
                        logger.info(f"Sent: {response}")
                    else:
                        # No more data from client
                        break
                    
            finally:
                # Clean up the connection
                client_socket.close()
                logger.info(f"Connection with {client_address} closed")
    
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        server_socket.close()
        logger.info("Server stopped")

if __name__ == "__main__":
    start_server()
