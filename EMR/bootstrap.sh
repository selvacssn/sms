#!/bin/bash

# Exit on error and log all commands
set -ex

# Set up logging
exec > >(tee -i /var/log/bootstrap-script.log)
exec 2>&1

echo "Starting bootstrap script..."

# Function to install packages on a node
install_packages() {
    echo "Installing Python packages..."
    
    # Update pip first
    sudo python3 -m pip install --upgrade pip
    if [ $? -ne 0 ]; then
        echo "Failed to upgrade pip"
        return 1
    fi
    
    # Install required packages
    sudo python3 -m pip install requests boto3 --no-cache-dir
    if [ $? -ne 0 ]; then
        echo "Failed to install Python packages"
        return 1
    fi
    
    # Verify installations
    echo "Verifying Python packages..."
    python3 -c "import requests; import boto3; print('Python packages verified successfully')"
    if [ $? -ne 0 ]; then
        echo "Failed to verify Python packages"
        return 1
    fi
    
    return 0
}

# Function to set up logging directory
setup_logging() {
    echo "Creating log directory..."
    sudo mkdir -p /var/log/risk-processor
    if [ $? -ne 0 ]; then
        echo "Failed to create log directory"
        return 1
    fi
    
    sudo chmod 777 /var/log/risk-processor
    if [ $? -ne 0 ]; then
        echo "Failed to set permissions on log directory"
        return 1
    fi
    
    return 0
}

# Function to set up processor script
setup_processor() {
    echo "Setting up processor script..."
    aws s3 cp s3://ssn0212/scripts/processor.py /home/hadoop/processor.py
    if [ $? -ne 0 ]; then
        echo "Failed to copy processor script"
        return 1
    fi
    
    sudo chmod +x /home/hadoop/processor.py
    if [ $? -ne 0 ]; then
        echo "Failed to make processor script executable"
        return 1
    fi
    
    return 0
}

# Function to create S3 logs directory
create_s3_logs() {
    echo "Creating S3 logs directory..."
    aws s3api put-object --bucket ssn0212 --key logs/processor_logs/
    if [ $? -ne 0 ]; then
        echo "Failed to create S3 logs directory"
        return 1
    fi
    
    return 0
}

# Main execution
echo "Starting main bootstrap execution..."

# Install packages
install_packages
if [ $? -ne 0 ]; then
    echo "Failed during package installation"
    exit 1
fi

# Set up logging
setup_logging
if [ $? -ne 0 ]; then
    echo "Failed during logging setup"
    exit 1
fi

# Set up processor script
setup_processor
if [ $? -ne 0 ]; then
    echo "Failed during processor setup"
    exit 1
fi

# Create S3 logs directory
create_s3_logs
if [ $? -ne 0 ]; then
    echo "Failed during S3 logs directory creation"
    exit 1
fi

# Install packages on all nodes if this is the master node
IS_MASTER=false
if grep isMaster /mnt/var/lib/info/instance.json | grep true; then
    IS_MASTER=true
fi

if [ "$IS_MASTER" = true ]; then
    echo "This is the master node. Installing packages on all nodes..."
    for host in `cat /etc/hosts | grep emr-worker | awk '{print $1}'`; do
        echo "Installing packages on $host..."
        ssh $host "sudo python3 -m pip install --upgrade pip && sudo python3 -m pip install requests boto3 --no-cache-dir"
        if [ $? -ne 0 ]; then
            echo "Failed to install packages on worker node $host"
            exit 1
        fi
    done
fi

echo "Bootstrap actions completed successfully"
