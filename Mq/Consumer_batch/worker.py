import pika
import json
import time
import ssl
import os
import threading
from queue import Empty, Queue

# Retrieve configuration from environment variables
MQ_HOST = os.getenv("MQ_HOST", "default_host")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default_queue")
USERNAME = os.getenv("USERNAME", "default_user")
PASSWORD = os.getenv("PASSWORD", "default_password")

# Global flag for graceful shutdown
should_continue = True
message_processed = threading.Event()

def process_message(body):
    """Simulate processing"""
    time.sleep(0.01)  # Simulating 10ms processing delay
    return {"processed": body}

def check_queue_status(channel, empty_count=0):
    """Check if queue is empty"""
    global should_continue
    
    if not message_processed.wait(timeout=1.0):  # Wait for 1 second for message processing
        empty_count += 1
        if empty_count >= 50:  # Queue empty for 50 consecutive checks
            print(f"Queue has been empty for {empty_count} consecutive checks. Initiating shutdown...")
            should_continue = False
            return
    else:
        empty_count = 0  # Reset counter if message was processed
        message_processed.clear()
    
    # Schedule next check
    if should_continue:
        threading.Timer(0.1, check_queue_status, args=(channel, empty_count)).start()

def main():
    global should_continue
    
    # Set up credentials and SSL options for secure connection
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    ssl_context = ssl.create_default_context()
    ssl_options = pika.SSLOptions(context=ssl_context)

    # Establish connection parameters
    connection_params = pika.ConnectionParameters(
        host=MQ_HOST,
        port=5671,
        virtual_host="/",
        credentials=credentials,
        ssl_options=ssl_options,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Declare the queue to ensure it exists
    queue_info = channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    def callback(ch, method, properties, body):
        """Callback for processing messages"""
        try:
            customer_id = json.loads(body)
            print(f"Received customer ID: {customer_id}")
            result = process_message(customer_id)
            print(f"Processed result: {result}")

            # Acknowledge the message after successful processing
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # Signal that a message was processed
            message_processed.set()
            
            if not should_continue:
                ch.stop_consuming()
                
        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # Configure QoS for optimal performance
    channel.basic_qos(prefetch_count=10)  # Process up to 10 messages at a time
    
    # Start the queue status checker in a separate thread
    status_checker = threading.Thread(target=check_queue_status, args=(channel,))
    status_checker.daemon = True
    status_checker.start()

    # Start consuming messages
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("Worker started. Processing messages...")
    try:
        while should_continue:
            connection.process_data_events(time_limit=0.1)  # Process events with timeout
            if not should_continue:
                break
                
    except KeyboardInterrupt:
        print("Received shutdown signal. Initiating graceful shutdown...")
        should_continue = False
        
    finally:
        try:
            print("Closing connection...")
            connection.close()
            print("Connection closed successfully.")
        except Exception as e:
            print(f"Error closing connection: {e}")

if __name__ == "__main__":
    main()
