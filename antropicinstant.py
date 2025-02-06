import boto3
import json

# Create session and Bedrock clients
session = boto3.Session(profile_name='awsbedrock-profile')
# Client for listing models
bedrock = session.client(service_name='bedrock', region_name='us-east-1')
# Client for invoking models
bedrock_runtime = session.client(service_name='bedrock-runtime', region_name='us-east-1')

# List available models
try:
    models = bedrock.list_foundation_models()
    print("Available models:")
    for model in models['modelSummaries']:
        print(f"- {model['modelId']}")
except Exception as e:
    print(f"Error listing models: {e}")

# Prepare the request body for Claude Instant
body = json.dumps({
    "prompt": "\n\nHuman: Write a short poem about technology.\n\nAssistant:",
    "max_tokens_to_sample": 300,
    "temperature": 0.7,
    "stop_sequences": ["\n\nHuman:"]
})

try:
    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-instant-v1",
        contentType="application/json",
        accept="application/json",
        body=body
    )
    
    response_body = json.loads(response['body'].read().decode())
    print("Claude's Response:", response_body.get('completion', 'No response'))
except Exception as e:
    print(f"Error: {e}")
