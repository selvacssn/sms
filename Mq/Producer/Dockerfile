FROM python:3.9-slim
WORKDIR /app
COPY producer.py .
RUN pip install pika
CMD ["python", "producer.py"]
