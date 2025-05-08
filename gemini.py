from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List, Union, BinaryIO
import os
import base64
from PIL import Image
import io
import json
import httpx
import api_keys
import importlib.util
import sys

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_keys.GEMINI_API_KEY
        self.client = genai.Client(api_key=api_key)
    
    def generate_text(self, 
                     prompt: str, 
                     model: str = "gemini-2.0-flash") -> str:
        """
        Generate text using Gemini models
        
        Args:
            prompt (str): The prompt to generate text from
            model (str): The Gemini model to use
            
        Returns:
            str: The generated text
        """
        response = self.client.models.generate_content(
            model=model,
            contents=[prompt]
        )
        
        return response.text
    
    def generate_text_stream(self, 
                           prompt: str, 
                           model: str = "gemini-2.0-flash"):
        """
        Generate streaming text response using Gemini models
        
        Args:
            prompt (str): The prompt to generate text from
            model (str): The Gemini model to use
            
        Returns:
            generator: A generator yielding response chunks
        """
        response = self.client.models.generate_content(
            model=model,
            contents=[prompt],
            stream=True
        )
        
        return response
    
    def chat(self, 
            messages: List[Dict[str, Any]], 
            model: str = "gemini-2.0-flash") -> str:
        """
        Have a multi-turn conversation with Gemini
        
        Args:
            messages (List[Dict]): List of message dictionaries with 'role' and 'parts'
            model (str): The Gemini model to use
            
        Returns:
            str: The model's response
        """
        response = self.client.models.generate_content(
            model=model,
            contents=messages
        )
        
        return response.text
    
    def analyze_image(self, 
                     image_path: str, 
                     prompt: str = "Describe this image in detail", 
                     model: str = "gemini-2.0-flash") -> str:
        """
        Analyze an image using Gemini's multimodal capabilities
        
        Args:
            image_path (str): Path to the image file
            prompt (str): The prompt to use for image analysis
            model (str): The Gemini model to use
            
        Returns:
            str: The analysis result
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Upload the image using the Files API for larger images
        if os.path.getsize(image_path) > 20 * 1024 * 1024:  # 20MB
            my_file = self.client.files.upload(file=image_path)
            
            response = self.client.models.generate_content(
                model=model,
                contents=[my_file, prompt]
            )
        else:
            # For smaller images, use inline data
            img = Image.open(image_path)
            
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                img = background
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()
            
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    ),
                    prompt
                ]
            )
        
        return response.text
    
    def generate_image(self, 
                      prompt: str, 
                      model: str = "gemini-2.0-flash-preview-image-generation") -> Dict:
        """
        Generate an image using Gemini's image generation capabilities
        
        Args:
            prompt (str): The prompt describing the image to generate
            model (str): The Gemini model to use
            
        Returns:
            Dict: Response containing the generated image data
        """
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        # Extract image data from response
        result = {
            "text": response.text,
            "image_data": None
        }
        
        # Extract image data if available
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                result["image_data"] = part.inline_data.data
                break
        
        return result
    
    def edit_image(self, 
                  image_path: str, 
                  prompt: str, 
                  model: str = "gemini-2.0-flash-preview-image-generation") -> Dict:
        """
        Edit an image using Gemini's image editing capabilities
        
        Args:
            image_path (str): Path to the image file to edit
            prompt (str): The prompt describing the desired edits
            model (str): The Gemini model to use
            
        Returns:
            Dict: Response containing the edited image data
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        img = Image.open(image_path)
        
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        
        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        # Extract image data from response
        result = {
            "text": response.text,
            "image_data": None
        }
        
        # Extract image data if available
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                result["image_data"] = part.inline_data.data
                break
        
        return result
    
    def process_document(self, 
                        file_path: str, 
                        prompt: str = "Analyze this document", 
                        model: str = "gemini-2.0-flash") -> str:
        """
        Process a document file (PDF, TXT, etc.) using Gemini
        
        Args:
            file_path (str): Path to the document file
            prompt (str): The prompt to use for document processing
            model (str): The Gemini model to use
            
        Returns:
            str: The processing result
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file size
        file_size = os.path.getsize(file_path)
        
        # For files larger than 20MB, use the Files API
        if file_size > 20 * 1024 * 1024:  # 20MB
            sample_file = self.client.files.upload(file=file_path)
            
            response = self.client.models.generate_content(
                model=model,
                contents=[sample_file, prompt]
            )
        else:
            # For smaller files, use direct processing
            # Determine MIME type based on file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_type = self._get_mime_type(file_ext)
            
            # Read file as binary data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=file_data,
                        mime_type=mime_type
                    ),
                    prompt
                ]
            )
        
        return response.text
    
    def process_document_from_url(self, 
                                url: str, 
                                prompt: str = "Analyze this document", 
                                model: str = "gemini-2.0-flash") -> str:
        """
        Process a document from a URL using Gemini
        
        Args:
            url (str): URL of the document to process
            prompt (str): The prompt to use for document processing
            model (str): The Gemini model to use
            
        Returns:
            str: The processing result
        """
        try:
            import pathlib
            import tempfile
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as temp_file:
                temp_path = pathlib.Path(temp_file.name)
                
                # Download and save the file
                temp_path.write_bytes(httpx.get(url).content)
                
                # Determine MIME type based on URL extension
                file_ext = os.path.splitext(url)[1].lower()
                mime_type = self._get_mime_type(file_ext)
                
                try:
                    # Process the document using the Part.from_bytes method
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[
                            types.Part.from_bytes(
                                data=temp_path.read_bytes(),
                                mime_type=mime_type
                            ),
                            prompt
                        ]
                    )
                    
                    # Clean up the temporary file
                    os.unlink(temp_path)
                    
                    return response.text
                except Exception as e:
                    # Clean up the temporary file in case of error
                    os.unlink(temp_path)
                    raise e
        except Exception as e:
            print(f"Error processing URL document with Gemini: {e}")
            raise
    
    def get_object_bounding_box(self, 
                              image_path: str, 
                              object_description: str, 
                              model: str = "gemini-2.0-flash") -> Dict:
        """
        Get bounding box coordinates for an object in an image
        
        Args:
            image_path (str): Path to the image file
            object_description (str): Description of the object to locate
            model (str): The Gemini model to use
            
        Returns:
            Dict: Bounding box coordinates (x1, y1, x2, y2)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        img = Image.open(image_path)
        
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        
        prompt = f"""
        Find the bounding box coordinates for the {object_description} in this image.
        Return ONLY a JSON object with the following format:
        {{
            "x1": float,  // top-left x coordinate (normalized 0-1)
            "y1": float,  // top-left y coordinate (normalized 0-1)
            "x2": float,  // bottom-right x coordinate (normalized 0-1)
            "y2": float   // bottom-right y coordinate (normalized 0-1)
        }}
        """
        
        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                ),
                prompt
            ]
        )
        
        try:
            # Parse the response as JSON
            bbox = json.loads(response.text)
            return bbox
        except json.JSONDecodeError:
            print(f"Error parsing response as JSON: {response.text}")
            return {"error": "Failed to parse bounding box coordinates"}
    
    def analyze_reddit_posts_batch(self, 
                          temp_file_path: str, 
                          model: str = "gemini-2.0-flash") -> list:
        """
        Analyze multiple Reddit posts from a temporary Python file
        
        Args:
            temp_file_path (str): Path to the temporary Python file containing posts
            model (str): The Gemini model to use
            
        Returns:
            list: List of analysis results for each post
        """
        try:
            # Load the Python module dynamically
            module_name = os.path.basename(temp_file_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Access the reddit_posts variable from the loaded module
            post_data_list = module.reddit_posts
            
            if not post_data_list:
                return []
                
            # Create prompt for Gemini
            posts_json = []
            for i, post in enumerate(post_data_list):
                posts_json.append({
                    "id": i,
                    "title": post.get("title", ""),
                    "body": post.get("body", "")
                })
            
            # Create a PDF-like prompt with clear structure
            prompt = f"""
            # Reddit Post Analysis Task
            
            Analyze the following Reddit posts and determine which ones are good questions related to finance or business.
            
            ## Posts to Analyze:
            # Using Python file: {temp_file_path}
            
            ## Evaluation Criteria:
            1. Is this post related to finance or business? (true/false)
            2. Is this a question? (true/false)
            3. Rate the quality of this question from 1-10
            4. Provide a brief reason for your rating
            
            ## Required Output Format:
            Return ONLY a JSON array with one object per post, using the following structure:
            [
                {{
                    "id": 0,
                    "is_finance_business": true/false,
                    "is_question": true/false,
                    "quality_rating": 1-10,
                    "rating_reason": "brief explanation",
                    "should_process": true/false
                }},
                ...
            ]
            
            The "should_process" field should be true only if both "is_finance_business" and "is_question" are true AND quality_rating is 5 or higher.
            In your response, Do not include any introduction, explanation, or additional text.
            """
            
            # Read the Python file content
            with open(temp_file_path, 'rb') as f:
                file_data = f.read()
            
            # Process the Python file as a document with the prompt
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=file_data,
                        mime_type="text/x-python"
                    ),
                    prompt
                ]
            )
            
            # Parse the response as JSON
            try:
                # Clean the response text by removing markdown code block markers if present
                response_text = response.text
                if response_text.startswith("```"):
                    # Find the end of the first line and skip it
                    first_line_end = response_text.find('\n')
                    if first_line_end != -1:
                        response_text = response_text[first_line_end + 1:]
                    
                    # Find and remove the closing code block markers
                    closing_markers = response_text.rfind("```")
                    if closing_markers != -1:
                        response_text = response_text[:closing_markers]
                
                # Now parse the cleaned JSON
                results = json.loads(response_text)
                
                # Ensure we have a list
                if not isinstance(results, list):
                    print(f"Error: Expected a list but got {type(results)}")
                    return [{"should_process": False}] * len(post_data_list)
                    
                # Sort results by ID to ensure they match the original order
                results.sort(key=lambda x: x.get("id", 0))
                
                return results
            except json.JSONDecodeError:
                print(f"Error parsing Gemini response as JSON: {response.text}")
                # Return a default response for each post
                return [{"should_process": False}] * len(post_data_list)
                
        except Exception as e:
            print(f"Error analyzing Reddit posts with Gemini: {e}")
            import traceback
            traceback.print_exc()
            return []

            
    def _get_mime_type(self, file_ext: str) -> str:
        """
        Get the MIME type for a file extension
        
        Args:
            file_ext (str): The file extension (including the dot)
            
        Returns:
            str: The MIME type
        """
        mime_types = {
            '.pdf': 'application/pdf',
            '.js': 'application/javascript',
            '.py': 'text/x-python',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.md': 'text/markdown',
            '.csv': 'text/csv',
            '.xml': 'text/xml',
            '.rtf': 'text/rtf',
            '.json': 'application/json',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        
        return mime_types.get(file_ext, 'application/octet-stream')
    def generate_text_with_web_search(self, 
                                prompt: str, 
                                model: str = "gemini-2.0-flash") -> str:
        """
        Generate text using Gemini models with web search enabled
        
        Args:
            prompt (str): The prompt to generate text from
            model (str): The Gemini model to use
            
        Returns:
            str: The generated text
        """
        try:
            # Configure generation with web search enabled
            generation_config = types.GenerationConfig(
                temperature=0.2,  # Lower temperature for more factual responses
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,  # Allow for longer responses
                candidate_count=1
            )
            
            # Safety settings to allow informational content
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            # Enable web search for up-to-date information
            tools = [
                {
                    "web_search": {}
                }
            ]
            
            # Generate content with web search enabled
            response = self.client.models.generate_content(
                model=model,
                contents=[prompt],
                generation_config=generation_config,
                safety_settings=safety_settings,
                tools=tools
            )
            
            # Process the response to remove any unwanted formatting
            content = response.text
            
            # Remove any markdown code block markers if present
            if content.startswith("```"):
                first_line_end = content.find('\n')
                if first_line_end != -1:
                    content = content[first_line_end + 1:]
                
                closing_markers = content.rfind("```")
                if closing_markers != -1:
                    content = content[:closing_markers]
            
            # Remove any introduction or conclusion sections
            lines = content.split('\n')
            filtered_lines = []
            skip_section = False
            
            for line in lines:
                lower_line = line.lower()
                
                # Skip introduction sections
                if any(intro in lower_line for intro in ["introduction", "overview", "background", "context"]) and "#" in line:
                    skip_section = True
                    continue
                    
                # Skip conclusion sections
                if any(concl in lower_line for concl in ["conclusion", "summary", "final thoughts", "in conclusion", "to summarize"]) and "#" in line:
                    skip_section = True
                    continue
                    
                # Reset skip flag when we hit a new section
                if "#" in line and not any(skip_word in lower_line for skip_word in ["introduction", "conclusion", "summary", "overview"]):
                    skip_section = False
                
                if not skip_section:
                    filtered_lines.append(line)
            
            # Join the filtered lines back together
            content = '\n'.join(filtered_lines)
            
            return content.strip()
            
        except Exception as e:
            print(f"Error generating text with web search: {e}")
            import traceback
            traceback.print_exc()
            return ""


if __name__ == "__main__":
    pass



