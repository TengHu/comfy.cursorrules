import os
import json
import io
from PIL import Image
import base64

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

        
def try_decode_data(data):
    """Try different methods to decode the data."""
    if isinstance(data, dict):
        return data
    
    try:
        # Try direct JSON parsing
        return json.loads(data)
    except:
        try:
            # Try base64 decode then JSON parse
            decoded = base64.b64decode(data).decode('utf-8')
            return json.loads(decoded)
        except:
            pass
    return None

def main():
    # Directory containing the workflow templates
    template_dir = "tools/workflow_templates"
    
    # Process all PNG files in the directory
    for filename in os.listdir(template_dir):
        if filename.lower().endswith('.png'):
            png_path = os.path.join(template_dir, filename)
            print(f"\nProcessing {filename}...")
            
            # Read the image file
            with open(png_path, 'rb') as f:
                image_data = f.read()
            
            # Extract workflow metadata
            workflow_data = extract_workflow_from_image(image_data)
            
            if workflow_data:
                # Create JSON filename with same base name
                json_filename = os.path.splitext(filename)[0] + '_metadata.json'
                json_path = os.path.join(template_dir, json_filename)
                
                # Save workflow metadata to JSON file
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(workflow_data, f, indent=2)
                print(f"Saved metadata to {json_filename}")
            else:
                print(f"No workflow metadata found in {filename}")

if __name__ == "__main__":
    main() 