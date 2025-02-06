# EMR-based ID Processing System

This is an AWS EMR (Elastic MapReduce) implementation for processing IDs in parallel using Apache Spark. The system consists of two main components:

1. A producer that generates IDs and uploads them to S3
2. An EMR cluster that processes these IDs using Spark and posts them to an API endpoint

## Components

### Producer
- Generates test IDs and uploads them to S3
- Uses timestamp-based filenames for easy tracking
- Provides detailed logging
- Returns the S3 path for EMR processing

### EMR Processor
- Runs on EMR cluster using Spark
- Reads IDs from S3 in parallel
- Processes IDs using Spark partitioning
- Posts to API endpoint with error handling
- Provides comprehensive logging

## Setup

1. Install AWS CLI and configure credentials:
```bash
aws configure
```

2. Upload the processor script and bootstrap script to S3:
```bash
aws s3 cp processor.py s3://ssn0212/scripts/
aws s3 cp bootstrap.sh s3://ssn0212/scripts/
```

3. Ensure the EMR roles are set up:
- EMR_EC2_DefaultRole
- EMR_DefaultRole

## Usage

### 1. Run the Producer

Generate test IDs and upload to S3:
```bash
python producer.py
```

### 2. Launch EMR Cluster

Launch the EMR cluster using the AWS CLI:
```bash
aws emr create-cluster --cli-input-json file://cluster_config.json
```

The EMR cluster will:
1. Start up with the specified configuration
2. Run the bootstrap script to install dependencies
3. Execute the Spark processor job
4. Terminate automatically upon completion

## Configuration Files

### cluster_config.json
- Defines EMR cluster configuration
- Specifies instance types and counts
- Sets up logging and monitoring
- Configures the Spark step to run the processor

### bootstrap.sh
- Installs required Python packages
- Sets up logging directories
- Copies processor script from S3

## Environment Variables

- `API_GATEWAY_URL`: Override the default API endpoint URL
  - Default: https://o33gysuh1e.execute-api.us-east-1.amazonaws.com/prod/risk-profile

## Monitoring

- EMR console shows cluster status and step progress
- CloudWatch logs contain detailed processing logs
- S3 logs directory contains cluster and step logs

## Architecture

1. Producer generates IDs and uploads to S3
2. EMR cluster launches with specified configuration
3. Bootstrap script installs dependencies
4. Spark job reads IDs from S3
5. Data is processed in parallel across worker nodes
6. Results are posted to API endpoint
7. Cluster terminates automatically upon completion
