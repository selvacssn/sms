FROM python:3.9-slim
WORKDIR /app
COPY worker.py .
COPY entryscript.sh .
RUN pip install pika
ENTRYPOINT ["bash", "entryscript.sh"]
