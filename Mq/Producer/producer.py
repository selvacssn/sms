import pika
import json
import ssl
import os

MQ_HOST = os.getenv("MQ_HOST", "default_host")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default_queue")
USERNAME = os.getenv("USERNAME", "default_user")
PASSWORD = os.getenv("PASSWORD", "default_password")
MQ_HOST = "b-db6b5461-37f7-4053-9e88-f348dd896243.mq.us-east-1.amazonaws.com"
QUEUE_NAME = "oe"
USERNAME = "ssn"  # Replace with your username
PASSWORD = "AlwaysC00l!23" 

def push_ids_to_queue(customer_ids):
    # Set up credentials and SSL options
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    ssl_context = ssl.create_default_context()
    ssl_options = pika.SSLOptions(context=ssl_context)

    # Establish connection parameters
    connection_params = pika.ConnectionParameters(
        host=MQ_HOST,
        port=5671,  # AMQPS default port
        virtual_host="/",  # Replace with the appropriate virtual host if needed
        credentials=credentials,
        ssl_options=ssl_options
    )

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Push messages to the queue
    for customer_id in customer_ids:
        message = json.dumps(customer_id)
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        print(f"Pushed customer ID: {customer_id}")

    # Close the connection
    connection.close()

# Generate test customer IDs
customer_ids = [{"id": i} for i in range(1000)]

# Push customer IDs to the queue
push_ids_to_queue(customer_ids)
