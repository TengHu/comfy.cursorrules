#!/usr/bin/env python3
"""
Crawler to download workflow template JSON files from GitHub repositories.
Usage: python github_workflow_crawler.py [URL] [--output DIR] [--file-type {json,image}]
   or: python github_workflow_crawler.py --repo URL [--output DIR] [--file-type {json,image}]

Example:
    python tools/crawlers/github_workflow_crawler.py --repo https://github.com/Comfy-Org/workflow_templates/tree/main/templates --output tools/workflow_templates --file-type json
    python tools/crawlers/github_workflow_crawler.py --repo https://github.com/comfyanonymous/ComfyUI_examples --output tools/workflow_templates --file-type image

"""

import os
import json
import requests
import base64
import argparse
import re
from pathlib import Path
import logging
from PIL import Image
import io

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GitHub API constants
GITHUB_API_URL = "https://api.github.com"
DEFAULT_REPO_URL = "https://github.com/Comfy-Org/workflow_templates"
DEFAULT_OUTPUT_DIR = "tools/workflow_templates"

# File type constants
FILE_TYPE_JSON = "json"
FILE_TYPE_IMAGE = "image"
SUPPORTED_FILE_TYPES = [FILE_TYPE_JSON, FILE_TYPE_IMAGE]
SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

def parse_github_url(url):
    """Extract owner, repo name, and path from a GitHub URL."""
    # Basic pattern to extract owner and repo
    basic_pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)"
    match = re.match(basic_pattern, url)
    
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    owner = match.group(1)
    repo = match.group(2)
    path = ""
    
    # Check if URL contains a path (e.g., /tree/main/templates)
    tree_pattern = r"(?:https?://)?(?:www\.)?github\.com/[^/]+/[^/]+/tree/([^/]+)/(.+)"
    tree_match = re.match(tree_pattern, url)
    
    if tree_match:
        branch = tree_match.group(1)
        path = tree_match.group(2)
        # Clean up repo name if it contains extra parts
        repo = repo.split('/')[0]
        logger.info(f"Detected branch: {branch}, path: {path}")
    
    return owner, repo, path

def get_repo_contents(owner, repo, path=""):
    """Fetch contents of a directory in the repository."""
    api_path = f"/repos/{owner}/{repo}/contents"
    if path:
        api_path += f"/{path}"
    
    url = f"{GITHUB_API_URL}{api_path}"
    logger.info(f"Fetching repository contents from: {url}")
    
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch repository contents: {response.status_code} - {response.text}")
        response.raise_for_status()
    
    return response.json()

def extract_workflow_from_image(image_data):
    """Extract workflow data from image bytes and return it as a JSON object."""
    try:
        # Open the image from bytes
        img = Image.open(io.BytesIO(image_data))
        
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
                logger.error("Found metadata but couldn't parse as JSON")
        
        logger.error("No workflow data found in the image")
        return None
    except Exception as e:
        logger.error(f"Error extracting workflow: {e}")
        return None

def download_file(file_info, file_type=FILE_TYPE_JSON):
    """Download a single file from the repository."""
    file_name = file_info["name"]
    file_ext = Path(file_name).suffix.lower()
    
    # Check if file type matches the requested type
    if file_info["type"] != "file":
        return None
        
    if file_type == FILE_TYPE_JSON and not file_name.endswith(".json"):
        return None
    elif file_type == FILE_TYPE_IMAGE and file_ext not in SUPPORTED_IMAGE_EXTENSIONS:
        return None
    
    logger.info(f"Downloading file: {file_name}")
    
    # Get the raw file content
    response = requests.get(file_info["download_url"])
    if response.status_code != 200:
        logger.error(f"Failed to download file {file_name}: {response.status_code}")
        return None
    
    try:
        if file_type == FILE_TYPE_JSON:
            # Parse JSON to validate it
            content = response.text
            json_content = json.loads(content)
            return {
                "name": file_name,
                "content": json_content
            }
        else:  # file_type == FILE_TYPE_IMAGE
            # Extract workflow from image
            workflow_json = extract_workflow_from_image(response.content)
            if workflow_json:
                return {
                    "name": f"{Path(file_name).stem}.json",  # Convert image name to .json
                    "content": workflow_json
                }
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing file {file_name}: {e}")
        return None

def process_directory(owner, repo, path, output_dir, recursive=True, file_type=FILE_TYPE_JSON):
    """Process a directory and download all files of specified type."""
    contents = get_repo_contents(owner, repo, path)
    
    # Track statistics
    total_files = 0
    downloaded_files = 0
    
    for item in contents:
        if item["type"] == "file":
            file_ext = Path(item["name"]).suffix.lower()
            if ((file_type == FILE_TYPE_JSON and item["name"].endswith(".json")) or
                (file_type == FILE_TYPE_IMAGE and file_ext in SUPPORTED_IMAGE_EXTENSIONS)):
                total_files += 1
                file_data = download_file(item, file_type)
                
                if file_data:
                    # Save the file
                    output_path = output_dir / file_data["name"]
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(file_data["content"], f, indent=2)
                    
                    downloaded_files += 1
                    logger.info(f"Saved: {output_path}")
        
        # Recursively process subdirectories if requested
        elif recursive and item["type"] == "dir":
            subdir_path = f"{path}/{item['name']}" if path else item["name"]
            logger.info(f"Processing subdirectory: {subdir_path}")
            sub_total, sub_downloaded = process_directory(owner, repo, subdir_path, output_dir, recursive, file_type)
            total_files += sub_total
            downloaded_files += sub_downloaded
    
    return total_files, downloaded_files

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Download workflow template JSON files from a GitHub repository")
    
    # Add URL as a positional argument
    parser.add_argument("url", nargs="?", type=str, default=None,
                        help="GitHub repository URL (positional argument)")
    
    # Keep the --repo flag for backward compatibility
    parser.add_argument("--repo", type=str, default=None,
                        help=f"GitHub repository URL (default: {DEFAULT_REPO_URL})")
    
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f"Local directory to save files (default: {DEFAULT_OUTPUT_DIR})")
    
    parser.add_argument("--recursive", action="store_true", default=True,
                        help="Recursively download files from subdirectories (default: True)")
    
    parser.add_argument("--file-type", type=str, choices=SUPPORTED_FILE_TYPES, default=FILE_TYPE_JSON,
                        help=f"File type to download (default: {FILE_TYPE_JSON})")
    
    args = parser.parse_args()
    
    # Determine which URL to use (positional has priority over --repo flag)
    if args.url is None and args.repo is None:
        args.url = DEFAULT_REPO_URL
    elif args.url is None:
        args.url = args.repo
    
    return args

def main():
    """Main function to crawl and download workflow templates."""
    args = parse_arguments()
    
    # Parse GitHub URL to get owner, repo name, and path
    repo_owner, repo_name, repo_path = parse_github_url(args.url)
    
    # Set output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading from: {repo_owner}/{repo_name}/{repo_path}")
    logger.info(f"Saving to: {output_dir}")
    logger.info(f"File type: {args.file_type}")
    
    try:
        # Process the directory and download files
        total_files, downloaded_files = process_directory(
            repo_owner, repo_name, repo_path, output_dir, args.recursive, args.file_type
        )
        
        file_type_str = "workflow" if args.file_type == FILE_TYPE_IMAGE else args.file_type
        logger.info(f"Crawling complete. Downloaded {downloaded_files}/{total_files} {file_type_str} files.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 