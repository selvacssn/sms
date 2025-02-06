import os
import sys
import socket
import urllib.request
from dotenv import load_dotenv

def test_connection(url):
    try:
        urllib.request.urlopen(url, timeout=5)
        return True
    except Exception as e:
        return str(e)

def test_socket_connection(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return str(e)

print("=== Network Test Starting ===")
print("Running comprehensive network diagnostics...")

# Test basic internet connectivity
print("\nTesting internet connectivity...")
google_test = test_connection("http://www.google.com")
if google_test is True:
    print("✓ Internet connection working")
else:
    print(f"✗ Internet connection failed: {google_test}")

# Test common service ports
print("\nTesting common service ports...")
common_ports = {
    80: "HTTP",
    443: "HTTPS",
    53: "DNS"
}

for port, service in common_ports.items():
    print(f"\nTesting {service} (port {port})...")
    result = test_socket_connection("8.8.8.8", port)
    if isinstance(result, bool) and result:
        print(f"✓ {service} port {port} is accessible")
    else:
        print(f"✗ {service} port {port} is not accessible: {result}")

# Test OpenAI API endpoint with headers
print("\nTesting OpenAI API endpoint...")
try:
    headers = {'User-Agent': 'Python/NetworkTest'}
    req = urllib.request.Request("https://api.openai.com/v1/models", headers=headers)
    response = urllib.request.urlopen(req, timeout=5)
    print("✓ OpenAI API endpoint reachable")
except urllib.error.HTTPError as e:
    if e.code == 401:
        print("✓ OpenAI API endpoint reachable (authentication required)")
    else:
        print(f"✗ OpenAI API endpoint error: {e}")
except Exception as e:
    print(f"✗ OpenAI API endpoint unreachable: {e}")

# Check environment variables
print("\nChecking environment variables...")
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✓ API key found (starts with: {api_key[:7]}...)")
else:
    print("✗ API key not found in environment variables")

# Print system info
print("\nSystem Information:")
print(f"Python version: {sys.version}")
print(f"Operating system: {os.name}")
print(f"Socket implementation: {socket.socket.__module__}")
try:
    hostname = socket.gethostname()
    print(f"Hostname: {hostname}")
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"IP address: {ip_address}")
    except socket.gaierror as e:
        print(f"Could not resolve IP address: {str(e)}")
    except socket.error as e:
        print(f"Socket error while getting IP: {str(e)}")
except Exception as e:
    print(f"Could not get network information: {str(e)}")

print("\n=== Network Test Complete ===")
