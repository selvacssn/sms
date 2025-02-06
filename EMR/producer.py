import json
import boto3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def write_ids_to_s3(customer_ids, bucket_name="ssn0212"):
    """Write customer IDs to S3"""
    s3 = boto3.client('s3')
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"customer_ids_{timestamp}.json"
    s3_path = f"input/{filename}"
    
    # Convert customer IDs to JSON string
    data = json.dumps(customer_ids, indent=2)
    
    try:
        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_path,
            Body=data
        )
        full_path = f"s3://{bucket_name}/{s3_path}"
        logger.info(f"Successfully wrote {len(customer_ids)} IDs to {full_path}")
        return full_path
    except Exception as e:
        logger.error(f"Error writing to S3: {str(e)}")
        raise

def generate_test_ids(count=100000):
    """Generate test IDs"""
    return [{"id": i} for i in range(count)]

if __name__ == "__main__":
    try:
        start_time = datetime.now()
        logger.info("Starting ID generation process...")
        
        # Generate test IDs
        customer_ids = generate_test_ids()
        generation_time = datetime.now() - start_time
        logger.info(f"Generated {len(customer_ids)} test IDs in {generation_time.total_seconds():.2f} seconds")
        
        # Write to S3
        write_start = datetime.now()
        s3_path = write_ids_to_s3(customer_ids)
        write_time = datetime.now() - write_start
        total_time = datetime.now() - start_time
        
        logger.info("Process completed successfully")
        logger.info(f"File location: {s3_path}")
        logger.info(f"Write time: {write_time.total_seconds():.2f} seconds")
        logger.info(f"Total time: {total_time.total_seconds():.2f} seconds")
        
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        raise
