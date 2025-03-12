#!/usr/bin/env python3
import json
import urllib.request
import sys

def call_object_info(server_address="127.0.0.1:3001"):
    """
    Makes a GET request to the ComfyUI server's /object_info endpoint
    and returns the response as a JSON object.
    
    Args:
        server_address (str): The address of the ComfyUI server
        
    Returns:
        dict: The JSON response from the server
    """
    try:
        print(f"Making request to http://{server_address}/object_info")
        with urllib.request.urlopen(f"http://{server_address}/object_info") as response:
            data = json.loads(response.read())
            return data
    except Exception as e:
        print(f"Error making request: {e}")
        return None

def main():
    # Use command line argument for server address if provided
    server_address = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:3001"
    
    # Call the endpoint
    response = call_object_info(server_address)
    
    if response:
        # Print the number of objects returned
        print(f"Received information about {len(response)} nodes")

        print (response)

        return response

if __name__ == "__main__":
    main() 