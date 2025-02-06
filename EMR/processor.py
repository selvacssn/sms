from pyspark.sql import SparkSession
import requests
import os
import logging
import json
import sys
import traceback
import boto3
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BatchLogger:
    def __init__(self, bucket, batch_id):
        self.bucket = bucket
        self.batch_id = batch_id
        self.log_key = f"logs/processor_logs/batch_{batch_id}.log"
        self.s3 = boto3.client('s3')
        self.log_content = []
        
    def write_header(self, input_path, batch_size):
        header = f"""=== Batch Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===
Input File: {input_path}
Found {batch_size} IDs to process

"""
        self.log_content.append(header)
        
    def write_footer(self):
        footer = f"""
=== Batch Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="""
        self.log_content.append(footer)
        self._write_to_s3()
        
    def log_request(self, risk_profile_id, request_url, payload, response, success, start_time, end_time):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        log_entry = f"""
{timestamp} - Processing ID: {risk_profile_id}
Request: POST {request_url}
Payload: {json.dumps(payload)}
Request Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
Request End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
Response Time: {response_time_ms:.2f} ms
Response: {json.dumps(response, indent=2) if success else response}
Status: {'SUCCESS' if success else 'FAILED'}
{'-' * 80}
"""
        self.log_content.append(log_entry)
        
    def log_error(self, risk_profile_id, error):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"""
{timestamp} - Error processing ID: {risk_profile_id}
Error: {str(error)}
Traceback: {traceback.format_exc()}
{'-' * 80}
"""
        self.log_content.append(log_entry)
        
    def _write_to_s3(self, retries=3, delay=1):
        content = ''.join(self.log_content)
        for attempt in range(retries):
            try:
                self.s3.put_object(
        self.log_content.append(log_entry)
        
    def _write_to_s3(self, retries=3, delay=1):
        content = ''.join(self.log_content)
        for attempt in range(retries):
            try:
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key=self.log_key,
                    Body=content.encode('utf-8')
                )
                return
            except Exception as e:
                if attempt == retries - 1:  # Last attempt
                    logger.error(f"Failed to write to S3 after {retries} attempts: {str(e)}")
                    raise
                time.sleep(delay)

def post_risk_profile(risk_profile_id, batch_logger):
    """Post a risk profile ID to the API Gateway endpoint"""
    api_url = os.getenv(
        'API_GATEWAY_URL', 
        'https://o33gysuh1e.execute-api.us-east-1.amazonaws.com/prod/risk-profile'
    )
    payload = {"risk_profile_id": risk_profile_id}
    
    try:
        logger.info(f"Processing ID: {risk_profile_id}")
        start_time = datetime.now()
        response = requests.post(api_url, json=payload)
        end_time = datetime.now()
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Success - Risk Profile ID: {risk_profile_id}")
            batch_logger.log_request(risk_profile_id, api_url, payload, response_data, True, start_time, end_time)
            return True
        else:
            logger.error(f"Failed - Risk Profile ID: {risk_profile_id}")
            batch_logger.log_request(risk_profile_id, api_url, payload, 
                                  f"Status Code: {response.status_code}, Response: {response.text}", 
                                  False, start_time, end_time)
            return False
            
    except Exception as e:
        logger.error(f"Error - Risk Profile ID: {risk_profile_id}")
        logger.error(traceback.format_exc())
        batch_logger.log_error(risk_profile_id, e)
        return False

def process_batch(ids):
    """Process a batch of IDs"""
    batch_start_time = datetime.now()
    timestamp = batch_start_time.strftime("%Y%m%d_%H%M%S")
    batch_logger = BatchLogger("ssn0212", timestamp)
    
    try:
        # Convert iterator to list and extract IDs
        id_list = [row['id'] for row in ids]
        batch_size = len(id_list)
        logger.info(f"Processing batch of {batch_size} IDs")
        batch_logger.write_header(input_path, batch_size)
        
        # Process IDs in chunks for better logging
        chunk_size = 100
        successful_requests = 0
        failed_requests = 0
        total_response_time = 0
        
        for i in range(0, len(id_list), chunk_size):
            chunk = id_list[i:i + chunk_size]
            chunk_start_time = datetime.now()
            
            # Process chunk
            for risk_profile_id in chunk:
                try:
                    request_start = datetime.now()
                    success = post_risk_profile(risk_profile_id, batch_logger)
                    request_time = (datetime.now() - request_start).total_seconds() * 1000  # ms
                    total_response_time += request_time
                    
                    if success:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Error processing ID {risk_profile_id}: {str(e)}")
                    logger.error(traceback.format_exc())
                    batch_logger.log_error(risk_profile_id, e)
            
            chunk_time = (datetime.now() - chunk_start_time).total_seconds()
            logger.info(f"Processed chunk {i//chunk_size + 1} ({len(chunk)} IDs) in {chunk_time:.2f} seconds")
        
        # Log batch statistics
        batch_time = (datetime.now() - batch_start_time).total_seconds()
        avg_response_time = total_response_time / (successful_requests + failed_requests) if (successful_requests + failed_requests) > 0 else 0
        
        logger.info(f"Batch Statistics:")
        logger.info(f"Total Time: {batch_time:.2f} seconds")
        logger.info(f"Average Response Time: {avg_response_time:.2f} ms")
        logger.info(f"Successful Requests: {successful_requests}")
        logger.info(f"Failed Requests: {failed_requests}")
        
        batch_logger.write_footer()
        
    except Exception as e:
        logger.error(f"Error in process_batch: {str(e)}")
        logger.error(traceback.format_exc())
        batch_logger.log_error("BATCH", e)
        batch_logger.write_footer()  # Ensure we write the log even on error
    
    return [(successful_requests, failed_requests)]

def main():
    try:
        logger.info("Starting Risk Profile Processor")
        start_time = datetime.now()

        # Initialize Spark session
        logger.info("Creating Spark session...")
        spark = SparkSession.builder \
            .appName("Risk Profile Processor") \
            .config("spark.executor.memory", "2g") \
            .config("spark.driver.memory", "2g") \
            .getOrCreate()
        
        logger.info(f"Successfully created Spark session. Version: {spark.version}")
        
        # Get input path from arguments
        if len(sys.argv) < 2:
            raise ValueError("Input path argument is required")
        
        global input_path
        input_path = sys.argv[1]
        logger.info(f"Input path: {input_path}")
        
        try:
            # Read input data
            logger.info(f"Reading data from: {input_path}")
            df = spark.read.option("multiline", "true").json(input_path)
            
            logger.info("DataFrame Schema:")
            df.printSchema()
            
            logger.info("Sample Data:")
            df.show(5, truncate=False)
            
            total_ids = df.count()
            logger.info(f"Successfully read {total_ids} records")
            
            # Process IDs in batches
            logger.info("Starting batch processing...")
            df.rdd.mapPartitions(process_batch).collect()
            
            # Log completion
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info("Processing complete!")
            logger.info(f"Total duration: {duration}")
            logger.info("Check S3 logs for detailed processing results")
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
    except Exception as e:
        logger.error(f"Critical error in main function: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'spark' in locals():
            logger.info("Shutting down Spark session")
            spark.stop()

if __name__ == "__main__":
    main()
