import requests
import time
import statistics
import json

def test_api():
    url = "https://o33gysuh1e.execute-api.us-east-1.amazonaws.com/prod/risk-profile"
    payload = {"risk_profile_id": "test-123"}
    response_times = []
    dns_times = []
    connect_times = []
    
    print("Testing API with 10 requests...")
    print(f"Sending payload: {json.dumps(payload, indent=2)}\n")
    
    session = requests.Session()  # Use session to reuse connections
    
    for i in range(10):
        start_time = time.time()
        response = session.post(url, json=payload)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        response_times.append(response_time)
        
        print(f"Request {i+1}:")
        print(f"Response Time: {response_time:.2f}ms")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}\n")
        
        # Add a small delay between requests
        time.sleep(0.1)
    
    avg_time = statistics.mean(response_times)
    print("\nTiming Statistics:")
    print(f"Average Response Time: {avg_time:.2f}ms")
    print(f"Min Response Time: {min(response_times):.2f}ms")
    print(f"Max Response Time: {max(response_times):.2f}ms")
    print(f"Standard Deviation: {statistics.stdev(response_times):.2f}ms")

if __name__ == "__main__":
    test_api()
