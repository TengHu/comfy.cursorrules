import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from PIL import Image
import json

def is_image_url(url):
    """Check if the URL points to an image file."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return any(path.endswith(ext) for ext in image_extensions)

def download_image(url, save_dir):
    """Download an image from URL and save it to the specified directory."""
    try:
        # Create a filename from the URL
        filename = os.path.basename(urlparse(url).path)
        
        # Ensure the filename is valid
        filename = re.sub(r'[^\w\-\.]', '_', filename)
        
        # Create the full save path
        save_path = os.path.join(save_dir, filename)
        
        # Check if file already exists
        if os.path.exists(save_path):
            print(f"File already exists: {save_path}")
            return save_path
        
        # Download the image
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save the image
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {url} -> {save_path}")
        
        # Be nice to the server
        time.sleep(0.5)
        
        return save_path
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def crawl_images(base_url, save_dir):
    """Crawl the website and download all images."""
    # Create the save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    downloaded_images = []
    
    try:
        # Get the main page
        response = requests.get(base_url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        links = soup.find_all('a')
        
        # Extract image URLs
        image_urls = []
        
        # Direct image links
        for link in links:
            href = link.get('href')
            if href and is_image_url(href):
                full_url = urljoin(base_url, href)
                image_urls.append(full_url)
        
        # Look for links to example pages that might contain images
        example_pages = []
        for link in links:
            href = link.get('href')
            if href and not is_image_url(href) and not href.startswith('#') and not href.startswith('http'):
                example_pages.append(urljoin(base_url, href))
        
        # Visit each example page and extract images
        for page_url in example_pages:
            try:
                page_response = requests.get(page_url)
                page_response.raise_for_status()
                
                page_soup = BeautifulSoup(page_response.text, 'html.parser')
                
                # Find images in the page
                for img in page_soup.find_all('img'):
                    src = img.get('src')
                    if src:
                        full_url = urljoin(page_url, src)
                        image_urls.append(full_url)
                
                # Find links to images
                for link in page_soup.find_all('a'):
                    href = link.get('href')
                    if href and is_image_url(href):
                        full_url = urljoin(page_url, href)
                        image_urls.append(full_url)
                
                # Be nice to the server
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing page {page_url}: {e}")
        
        # Remove duplicates
        image_urls = list(set(image_urls))
        
        print(f"Found {len(image_urls)} images to download")
        
        # Download each image
        for url in image_urls:
            image_path = download_image(url, save_dir)
            if image_path:
                downloaded_images.append(image_path)
            
        print(f"Crawling completed. Images saved to {save_dir}")
        
    except Exception as e:
        print(f"Error crawling {base_url}: {e}")
    
    return downloaded_images

def extract_workflow_from_image(image_path):
    """Extract workflow data from an image and return it as a JSON object."""
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Extract the workflow data from PNG chunks
        workflow_data = None
        
        # Check for ComfyUI metadata in PNG chunks
        if 'parameters' in img.info:
            workflow_data = img.info['parameters']
        elif 'workflow' in img.info:
            workflow_data = img.info['workflow']
        
        # Parse the JSON data if found
        if workflow_data:
            try:
                workflow_json = json.loads(workflow_data)
                return workflow_json
            except json.JSONDecodeError:
                print(f"Found metadata in {image_path} but couldn't parse as JSON")
        
        print(f"No workflow data found in the image: {image_path}")
        return None
    except Exception as e:
        print(f"Error extracting workflow from {image_path}: {e}")
        return None

def save_workflow_as_json(workflow_data, image_path, output_dir):
    """Save workflow data as a JSON file in the specified directory."""
    if not workflow_data:
        return None
    
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a filename based on the image name
        image_filename = os.path.basename(image_path)
        base_name = os.path.splitext(image_filename)[0]
        json_filename = f"{base_name}_workflow.json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Save the workflow as JSON
        with open(json_path, 'w') as f:
            json.dump(workflow_data, f, indent=2)
        
        print(f"Saved workflow from {image_path} to {json_path}")
        return json_path
    
    except Exception as e:
        print(f"Error saving workflow from {image_path}: {e}")
        return None

def process_images_for_workflows(image_dir, workflow_dir):
    """Process all images in a directory and extract workflows."""
    # Get all image files in the directory
    image_files = []
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            image_files.append(os.path.join(image_dir, filename))
    
    print(f"Found {len(image_files)} images to process for workflows")
    
    # Extract and save workflows
    saved_workflows = []
    for image_path in image_files:
        workflow_data = extract_workflow_from_image(image_path)
        if workflow_data:
            json_path = save_workflow_as_json(workflow_data, image_path, workflow_dir)
            if json_path:
                saved_workflows.append(json_path)
    
    print(f"Extracted and saved {len(saved_workflows)} workflows to {workflow_dir}")
    return saved_workflows

if __name__ == "__main__":
    base_url = "https://comfyanonymous.github.io/ComfyUI_examples/"
    image_dir = "tools/images"
    workflow_dir = "tools/workflow_templates"
    
    print(f"Starting to crawl {base_url} for images...")
    downloaded_images = crawl_images(base_url, image_dir)
    
    print(f"Processing downloaded images for workflows...")
    process_images_for_workflows(image_dir, workflow_dir) 