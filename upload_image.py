import os
import time
from datetime import datetime
from gradio_client import Client, handle_file
from PIL import Image  # We'll use Pillow for image conversion

def process_image(image_path, scale_factor="2x", save_result=True, output_dir="processed_images"):
    """
    Process an image with Face Real ESRGAN upscaling service using the official gradio_client API.
    
    Args:
        image_path: Path to the image file to upload
        scale_factor: Scale factor for upscaling ("2x", "4x", or "8x") - default is "2x"
        save_result: Whether to save the processed image locally (default: True)
        output_dir: Directory to save the processed image (default: "processed_images")
        
    Returns:
        Dictionary with processing results and local file path
    """
    print(f"Processing image: {image_path} with scale factor: {scale_factor}")
    
    try:
        # Create a client for the Face Real ESRGAN API
        client = Client("doevent/Face-Real-ESRGAN")
        
        # Process the image
        print("Submitting image for processing...")
        result = client.predict(
            image=handle_file(image_path),
            size=scale_factor,
            api_name="/predict"
        )
        
        print("Processing complete!")
        
        # Get the source path from the result
        source_path = None
        if isinstance(result, str):
            source_path = result
            print(f"Result is a file path: {source_path}")
        elif isinstance(result, dict) and 'path' in result:
            source_path = result['path']
            print(f"Result is a dict with path: {source_path}")
        else:
            print(f"Unexpected result format: {result}")
            # Try to handle the case where result might be a file path
            if isinstance(result, str) and os.path.exists(result):
                source_path = result
        
        # If we found a valid source path
        if source_path and os.path.exists(source_path):
            # Always convert to PNG
            img = Image.open(source_path)
            
            # If we need to save the result locally
            if save_result:
                # Create the output directory if it doesn't exist
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    print(f"Created directory: {output_dir}")
                
                # Generate a filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                
                # Always use PNG extension
                new_filename = f"{name}_processed_{scale_factor}_{timestamp}.png"
                
                # Construct the destination path
                dest_path = os.path.join(output_dir, new_filename)
                
                # Save as PNG
                img.save(dest_path, 'PNG')
                print(f"Saved converted PNG image to: {dest_path}")
                
                return {
                    "status": "success",
                    "result": result,
                    "local_path": dest_path
                }
            
            # If we're not saving, just return success
            return {
                "status": "success",
                "result": result
            }
        
        # If we couldn't find a valid source path
        return {
            "status": "success",
            "result": result,
            "error": "Could not find a valid source image path"
        }
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return {"status": "error", "error": str(e)}


def main():
    # Example usage
    image_path = "znQMkxQSSz.png"  # Use your image file
    
    print("Processing image with Face Real ESRGAN...")
    
    # Process and save to file
    process_result = process_image(image_path, scale_factor="2x", save_result=True)
    
    if process_result.get("status") == "success":
        print("\nImage processing completed successfully!")
        if process_result.get("local_path"):
            print(f"Processed image saved to: {process_result.get('local_path')}")
    else:
        print(f"\nImage processing failed: {process_result}")


# if __name__ == "__main__":
#     main()