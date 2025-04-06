#!/bin/bash

# Check if path argument is provided
if [ $# -ne 1 ]; then
    echo "Error: Please provide a destination path"
    echo "Usage: $0 <destination_path>"
    exit 1
fi

DEST_PATH="$1"
SCRIPT_DIR="$(dirname "$0")"  # Get the directory where the script is located

# List of files/directories to copy
# Add new items here as needed
ITEMS_TO_COPY=(
    ".cursorrules"
    "tools"
    # Add more files/directories here
    # Example:
    # "some_other_directory"
    # "config.json"
)

# Check if destination path exists
if [ ! -d "$DEST_PATH" ]; then
    echo "Creating destination directory: $DEST_PATH"
    mkdir -p "$DEST_PATH"
fi

# Copy each item in the list
for item in "${ITEMS_TO_COPY[@]}"; do
    if [ -e "$SCRIPT_DIR/$item" ]; then
        echo "Copying $item..."
        cp -r "$SCRIPT_DIR/$item" "$DEST_PATH/"
    else
        echo "Warning: $item not found in script directory"
    fi
done

echo "Copy operation completed!" 