import socket

def get_ip_address(url):
    try:
        # Extract the hostname from the URL
        hostname = url.split('//')[-1].split('/')[0]
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        return "Invalid URL or hostname could not be resolved"

if __name__ == "__main__":
    url = input("Enter a URL: ")
    ip_address = get_ip_address(url)
    print(f"The IP address of {url} is {ip_address}")
