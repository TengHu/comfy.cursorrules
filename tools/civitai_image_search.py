#!/usr/bin/env python3
"""
Civitai Model Downloader

This script allows you to search for and download models from Civitai using their API.
Requires a CIVITAI_API_KEY environment variable to be set.

Usage:
    python civitai_model_downloader.py --query "your search term" --limit 10 --nsfw false --download

Documentation: https://developer.civitai.com/docs/api/public-rest#get-apiv1models
"""

import os
import sys
import argparse
import requests
import json
from datetime import datetime
import time
from pathlib import Path
import urllib.parse

def get_api_key():
    """Get the Civitai API key from environment variables."""
    api_key = os.environ.get("CIVITAI_API_KEY")
    if not api_key:
        print("Error: CIVITAI_API_KEY environment variable not set.")
        print("Please set it using: export CIVITAI_API_KEY='your_api_key'")
        sys.exit(1)
    return api_key

def search_models(
    query=None, 
    limit=100, 
    page=1,
    nsfw=None, 
    sort=None, 
    period=None,
    types=None,
    baseModels=None,
    tags=None,
    username=None,
    api_key=None
):
    """
    Search for models on Civitai.
    
    Args:
        query (str, optional): Search term
        limit (int, optional): Maximum number of results to return (1-100, default: 100)
        page (int, optional): The page from which to start fetching models
        nsfw (str, optional): Filter by NSFW content (None, Soft, Mature, X, or boolean)
        sort (str, optional): Sort order (Highest Rated, Most Downloaded, Newest)
        period (str, optional): Time period (AllTime, Year, Month, Week, Day)
        types (list, optional): Model types to include (Checkpoint, TextualInversion, etc.)
        baseModels (list, optional): Base models to include (SD 1.5, SDXL, etc.)
        tags (list, optional): Tags to filter by
        username (str, optional): Filter to models from a specific user
        api_key (str, optional): Civitai API key
        
    Returns:
        dict: API response
    """
    base_url = "https://civitai.com/api/v1/models"
    
    params = {}
    
    # Add parameters only if they are provided
    if query:
        params["query"] = query
    if limit:
        params["limit"] = limit
    if page:
        params["page"] = page
    if nsfw is not None:
        params["nsfw"] = nsfw
    if sort:
        params["sort"] = sort
    if period:
        params["period"] = period
    if types:
        params["types"] = types if isinstance(types, str) else ",".join(types)
    if baseModels:
        params["baseModels"] = baseModels if isinstance(baseModels, str) else ",".join(baseModels)
    if tags:
        params["tags"] = tags if isinstance(tags, str) else ",".join(tags)
    if username:
        params["username"] = username
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        print(f"Making request to {base_url} with params: {params}")
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        sys.exit(1)

def get_model_versions(model_id, api_key=None):
    """
    Get versions of a specific model.
    
    Args:
        model_id (int): The ID of the model
        api_key (str, optional): Civitai API key
        
    Returns:
        dict: API response with model versions
    """
    base_url = f"https://civitai.com/api/v1/models/{model_id}"
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        print(f"Fetching model details from {base_url}")
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching model details: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None

def download_model_file(url, output_dir, filename=None):
    """
    Download a model file from a URL.
    
    Args:
        url (str): Model file URL
        output_dir (str): Directory to save the model
        filename (str, optional): Filename to save the model as
        
    Returns:
        str: Path to the downloaded model
    """
    try:
        print(f"Downloading from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            # Extract filename from URL or generate a timestamp-based one
            url_path = urllib.parse.urlparse(url).path
            filename = os.path.basename(url_path)
            if not filename or len(filename) < 5:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"civitai_model_{timestamp}.safetensors"
        
        # Ensure the filename has an extension if it doesn't already
        if not os.path.splitext(filename)[1]:
            filename += ".safetensors"
            
        file_path = os.path.join(output_dir, filename)
        
        # Save the model file with progress indicator
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1MB
        downloaded = 0
        
        print(f"Saving to {file_path}")
        with open(file_path, 'wb') as f:
            start_time = time.time()
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Calculate and display progress
                    if total_size > 0:
                        percent = downloaded / total_size * 100
                        elapsed_time = time.time() - start_time
                        speed = downloaded / (1024 * 1024 * elapsed_time) if elapsed_time > 0 else 0
                        print(f"\rProgress: {percent:.1f}% ({downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB) - {speed:.1f} MB/s", end="")
            
            print("\nDownload complete!")
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"\nError downloading model: {e}")
        return None

def display_results(results, download=False, output_dir="./models", api_key=None):
    """
    Display search results and optionally download models.
    
    Args:
        results (dict): API response
        download (bool): Whether to download models
        output_dir (str): Directory to save models
        api_key (str, optional): Civitai API key
    """
    items = results.get("items", [])
    metadata = results.get("metadata", {})
    
    print(f"\nFound {metadata.get('totalItems', 0)} models (showing {len(items)})")
    print("-" * 80)
    
    for i, model in enumerate(items, 1):
        model_id = model.get('id', 'Unknown')
        print(f"{i}. Model ID: {model_id}")
        print(f"   Name: {model.get('name', 'Unknown')}")
        print(f"   Type: {model.get('type', 'Unknown')}")
        print(f"   Description: {model.get('description', 'No description')[:100]}...")
        
        # Display model stats
        if "stats" in model:
            stats = model["stats"]
            print(f"   Downloads: {stats.get('downloadCount', 0)} | Rating: {stats.get('rating', 0)}")
        
        # Display model tags
        if "tags" in model and model["tags"]:
            print(f"   Tags: {', '.join(model['tags'])}")
        
        # Display model versions
        if "modelVersions" in model and model["modelVersions"]:
            versions = model["modelVersions"]
            print(f"   Versions available: {len(versions)}")
            
            for j, version in enumerate(versions, 1):
                print(f"      {j}. Version: {version.get('name', 'Unnamed')}")
                print(f"         Base Model: {version.get('baseModel', 'Unknown')}")
                
                if "files" in version and version["files"]:
                    files = version["files"]
                    print(f"         Files available: {len(files)}")
                    
                    for k, file in enumerate(files, 1):
                        file_name = file.get('name', 'Unnamed')
                        file_size = file.get('sizeKB', 0) / 1024  # Convert to MB
                        file_type = file.get('type', 'Unknown')
                        print(f"            {k}. {file_name} ({file_size:.2f} MB, {file_type})")
                        
                        if download:
                            # Ask user if they want to download this file
                            download_choice = input(f"         Download {file_name}? (y/n): ").lower()
                            if download_choice == 'y':
                                download_url = file.get('downloadUrl')
                                if download_url:
                                    # For some files, we need to use the API to get the actual download URL
                                    if "civitai.com/api/download" in download_url:
                                        headers = {}
                                        if api_key:
                                            headers["Authorization"] = f"Bearer {api_key}"
                                        
                                        # Create appropriate subdirectory based on model type
                                        model_type = model.get('type', 'Unknown')
                                        if model_type == "Checkpoint":
                                            type_dir = "checkpoints"
                                        elif model_type == "TextualInversion":
                                            type_dir = "embeddings"
                                        elif model_type == "LORA":
                                            type_dir = "loras"
                                        elif model_type == "Hypernetwork":
                                            type_dir = "hypernetworks"
                                        elif model_type == "AestheticGradient":
                                            type_dir = "aestheticgradients"
                                        elif model_type == "Controlnet":
                                            type_dir = "controlnet"
                                        else:
                                            type_dir = "other"
                                        
                                        model_dir = os.path.join(output_dir, type_dir)
                                        download_model_file(download_url, model_dir, file_name)
        
        print("-" * 80)
    
    # Display pagination information
    if "metadata" in results:
        meta = results["metadata"]
        print(f"Page {meta.get('currentPage', 1)} of {meta.get('totalPages', 1)}")
        if "nextPage" in meta:
            print(f"Next page: {meta['nextPage']}")
        if "prevPage" in meta:
            print(f"Previous page: {meta['prevPage']}")

def main():
    parser = argparse.ArgumentParser(description="Search for and download models from Civitai")
    parser.add_argument("--query", help="Search term")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to return (1-100)")
    parser.add_argument("--page", type=int, default=1, help="The page from which to start fetching models")
    parser.add_argument("--nsfw", help="Filter by NSFW content (None, Soft, Mature, X, or boolean)")
    parser.add_argument("--sort", choices=["Highest Rated", "Most Downloaded", "Newest"], 
                      help="Sort order")
    parser.add_argument("--period", choices=["AllTime", "Year", "Month", "Week", "Day"], 
                      help="Time period")
    parser.add_argument("--types", help="Model types to include (comma-separated: Checkpoint, TextualInversion, LORA, etc.)")
    parser.add_argument("--baseModels", help="Base models to include (comma-separated: SD 1.5, SDXL, etc.)")
    parser.add_argument("--tags", help="Tags to filter by (comma-separated)")
    parser.add_argument("--username", help="Filter to models from a specific user")
    parser.add_argument("--download", action="store_true", help="Enable interactive download of models")
    parser.add_argument("--output_dir", default="./models", help="Directory to save models")
    parser.add_argument("--model_id", type=int, help="Directly download a specific model by ID")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = get_api_key()
    
    # If a specific model ID is provided, get that model's details
    if args.model_id:
        print(f"Fetching details for model ID: {args.model_id}")
        model_details = get_model_versions(args.model_id, api_key)
        if model_details:
            # Create a results structure similar to search results
            results = {
                "items": [model_details],
                "metadata": {"totalItems": 1, "currentPage": 1, "totalPages": 1}
            }
            display_results(results, args.download, args.output_dir, api_key)
        sys.exit(0)
    
    # Search for models
    print(f"Searching for models on Civitai...")
    if args.query:
        print(f"Query: '{args.query}'")
    
    # Process list arguments
    types = args.types.split(',') if args.types else None
    base_models = args.baseModels.split(',') if args.baseModels else None
    tags = args.tags.split(',') if args.tags else None
    
    results = search_models(
        query=args.query,
        limit=args.limit,
        page=args.page,
        nsfw=args.nsfw,
        sort=args.sort,
        period=args.period,
        types=types,
        baseModels=base_models,
        tags=tags,
        username=args.username,
        api_key=api_key
    )
    
    # Display results and handle downloads
    display_results(results, args.download, args.output_dir, api_key)

if __name__ == "__main__":
    main() 