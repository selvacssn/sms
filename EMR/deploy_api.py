import boto3
import json

def deploy_api():
    try:
        print("Initializing AWS client...")
        client = boto3.client('apigateway', region_name='us-east-1')
        
        # Existing API ID from the URL
        api_id = 'o33gysuh1e'
        print(f"Using API ID: {api_id}")
        
        print("Getting API resources...")
        resources = client.get_resources(restApiId=api_id)
        print(f"Found resources: {json.dumps(resources, indent=2)}")
        
        # Find the risk-profile resource
        risk_profile_resource = None
        for resource in resources['items']:
            if resource.get('pathPart') == 'risk-profile':
                risk_profile_resource = resource
                break
        
        if not risk_profile_resource:
            raise Exception("Could not find risk-profile resource")
            
        resource_id = risk_profile_resource['id']
        
        print("Updating integration response...")
        
        # Setup integration response with delay
        client.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='200',
            responseTemplates={
                'application/json': """#set($context.responseOverride.sleep = 10)
#set($inputRoot = $input.path('$'))
{
    "message": "Successfully processed",
    "risk_profile_id": "$inputRoot.risk_profile_id"
}"""
            }
        )
        
        # Create deployment
        print("Creating deployment...")
        client.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )
        
        # Get the API URL
        api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/risk-profile"
        print(f"\nAPI Endpoint deployed successfully!")
        print(f"URL: {api_url}")
        
        return api_url
        
    except Exception as e:
        print(f"Error deploying API: {str(e)}")
        raise

if __name__ == "__main__":
    deploy_api()
