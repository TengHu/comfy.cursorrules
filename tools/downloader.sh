#!/bin/bash

# Function to download model from Huggingface
download_from_huggingface() {
    local repo_id="$1"          # Format: "username/repository"
    local filename="$2"         # Original filename in repository
    local output_name="$3"      # Desired output filename
    local output_dir="$4"       # Output directory
    local subfolder="${5:-""}"  # Optional subfolder within repository

    # Check if HF_ACCESS_TOKEN is set
    if [ -z "$HF_ACCESS_TOKEN" ]; then
        echo "Error: HF_ACCESS_TOKEN environment variable is not set"
        echo "Please set it using: export HF_ACCESS_TOKEN=your_api_key"
        exit 1
    fi


    # Construct the URL
    local base_url="https://huggingface.co/$repo_id/resolve/main"
    if [[ -n "$subfolder" ]]; then
        base_url="$base_url/$subfolder"
    fi
    local download_url="$base_url/$filename?download=true"
    
    # Ensure output directory exists
    mkdir -p "$output_dir"
    local output_file="$output_dir/$output_name"

    # Check if the file already exists
    if [[ -f "$output_file" ]]; then
        echo "File already exists: $output_file. Skipping download."
        return 0
    fi
    

    echo "Downloading from $download_url to $output_file, $output_dir, $OUTPUT_DIR"
    
    # Download the file
    curl -L -o "$output_file" -H "Authorization: Bearer ${HF_ACCESS_TOKEN}" "$download_url"

    
    # Verify download
    if [[ -f "$output_file" ]]; then
        echo "Model downloaded successfully: $output_file"
        return 0
    else
        echo "Failed to download model: $repo_id/$filename"
        return 1
    fi
}



download_from_civitai() {
    local url="$1"         # Original filename in repository
    local output_path="$2"      # Desired output filename
    
    # Check if CIVITAI_API_KEY is set
    if [ -z "$CIVITAI_API_KEY" ]; then
        echo "Error: CIVITAI_API_KEY environment variable is not set"
        echo "Please set it using: export CIVITAI_API_KEY=your_api_key"
        exit 1
    fi

    # Check if the file already exists
    if [[ -f "$output_path" ]]; then
        echo "File already exists: $output_path. Skipping download."
        return 0
    fi

    wget "${url}&token=${CIVITAI_API_KEY}" -O "$output_path" --content-disposition

    # Verify if the download was successful
    if [[ -f "$output_path" ]]; then
        echo "CIVITAI downloaded successfully to: $output_path"
    else
        echo "Failed to download. Please check your connection or the URL."
    fi
}