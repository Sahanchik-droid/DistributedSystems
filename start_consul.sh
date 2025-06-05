#!/bin/bash

# This script downloads and runs Consul locally if not already installed

# Check if Consul is installed
if ! command -v consul &> /dev/null; then
    echo "Consul could not be found, downloading..."
    
    # Get the latest version
    CONSUL_VERSION=$(curl -s https://releases.hashicorp.com/consul/ | grep -v beta | grep -v rc | grep href | head -n 1 | sed -E 's/.*href="\/consul\/([^"]+)\/".*/\1/')
    
    # Download for your platform (this example is for Linux amd64)
    # Change this if you're on a different platform
    curl -O https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip
    
    # Unzip it
    unzip consul_${CONSUL_VERSION}_linux_amd64.zip
    
    # Move to a directory in your PATH
    sudo mv consul /usr/local/bin/
    
    # Cleanup
    rm consul_${CONSUL_VERSION}_linux_amd64.zip
    
    echo "Consul installed successfully!"
else
    echo "Consul is already installed."
fi

# Create data directory for Consul
mkdir -p consul_data

# Check if Consul is running
if pgrep consul > /dev/null; then
    echo "Consul is already running"
else
    echo "Starting Consul..."
    # Start Consul in development mode in the background
    consul agent -dev -ui -client=0.0.0.0 -data-dir=./consul_data > consul.log 2>&1 &
    
    # Wait for Consul to start
    sleep 3
    echo "Consul started with PID: $(pgrep consul)"
fi

# Initialize Consul with configuration
echo "Initializing Consul configuration..."
python init_consul_config.py

echo "Consul is ready! UI available at: http://localhost:8500"
