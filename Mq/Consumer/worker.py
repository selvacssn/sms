import pika
import json
import time
import ssl
import os

# Retrieve configuration from environment variables
MQ_HOST = os.getenv("MQ_HOST", "default_host")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default_queue")
USERNAME = os.getenv("USERNAME", "default_user")
PASSWORD = os.getenv("PASSWORD", "default_password")

def process_message(body):
    """Simulate processing"""
    time.sleep(0.01)  # Simulating 10ms processing delay
    return {"processed": body}

def main():
    # Set up credentials and SSL options for secure connection
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    ssl_context = ssl.create_default_context()
    ssl_options = pika.SSLOptions(context=ssl_context)

    # Establish connection parameters
    connection_params = pika.ConnectionParameters(
        host=MQ_HOST,  # Extract host from URL
        port=5671,  # AMQPS default port
        virtual_host="/",  # Adjust as needed
        credentials=credentials,
        ssl_options=ssl_options
    )

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Declare the queue to ensure it exists
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    def callback(ch, method, properties, body):
        """Callback for processing messages"""
        try:
            customer_id = json.loads(body)
            print(f"Received customer ID: {customer_id}")
            result = process_message(customer_id)
            print(f"Processed result: {result}")

            # Acknowledge the message after successful processing
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing message: {e}")
            # Optionally reject the message and requeue it
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # Start consuming messages with prefetch to handle load efficiently
    channel.basic_qos(prefetch_count=1)  # Process one message at a time
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("Worker started. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped.")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
