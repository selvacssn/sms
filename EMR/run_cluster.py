import boto3
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_emr_cluster():
    try:
        # Load cluster configuration
        with open('cluster_config.json', 'r') as f:
            cluster_config = json.load(f)
            
        # Create EMR client
        emr = boto3.client('emr', region_name='us-east-1')
        
        # Create cluster
        logger.info("Creating EMR cluster...")
        start_time = datetime.now()
        response = emr.run_job_flow(**cluster_config)
        cluster_id = response['JobFlowId']
        logger.info(f"Created cluster with ID: {cluster_id}")
        
        # Wait for cluster to complete
        while True:
            response = emr.describe_cluster(ClusterId=cluster_id)
            status = response['Cluster']['Status']['State']
            
            if status in ['TERMINATED', 'TERMINATED_WITH_ERRORS']:
                end_time = datetime.now()
                duration = end_time - start_time
                logger.info(f"Cluster {status}")
                logger.info(f"Total duration: {duration}")
                break
                
            logger.info(f"Cluster status: {status}")
            time.sleep(30)  # Check every 30 seconds
            
        return cluster_id
        
    except Exception as e:
        logger.error(f"Error running EMR cluster: {str(e)}")
        raise

if __name__ == "__main__":
    run_emr_cluster()
