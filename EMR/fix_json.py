import json
import boto3
import re

def fix_json_file():
    s3 = boto3.client('s3')
    
    # Read the original file
    response = s3.get_object(Bucket='ssn0212', Key='input/customer_ids_20241202_190159.json')
    content = response['Body'].read().decode('utf-8')
    
    # Use regex to extract all IDs
    id_matches = re.findall(r'"id":\s*(\d+)', content)
    
    # Create JSON objects
    items = [{"id": int(id_val)} for id_val in id_matches]
    
    # Write back as properly formatted JSON array
    fixed_content = json.dumps(items, indent=2)
    
    print(f"Found {len(items)} items")
    print("First few items:", json.dumps(items[:5], indent=2))
    
    # Upload the fixed file
    s3.put_object(
        Bucket='ssn0212',
        Key='input/fixed_customer_ids.json',
        Body=fixed_content.encode('utf-8')
    )
    print("Fixed JSON file uploaded successfully")

if __name__ == "__main__":
    fix_json_file()
