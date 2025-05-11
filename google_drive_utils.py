from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import mimetypes
from typing import List, Dict, Any, Optional, Tuple
import api_keys

class GoogleDriveClient:
    """
    A utility class for interacting with Google Drive, particularly for uploading images
    and retrieving their shareable links.
    """
    
    def __init__(self):
        scopes = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
            ]
            
        # Use from_service_account_info instead of from_service_account_file
        self.credentials = Credentials.from_service_account_info(
            api_keys.GOOGLE_CLOUD_API_CREDENTIALS, scopes=scopes
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
    
    def upload_image(self, image_path: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload an image to Google Drive.
        
        Args:
            image_path: Path to the image file
            folder_id: Optional Google Drive folder ID to upload to
            
        Returns:
            Dictionary containing file metadata including id
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            # Default to generic binary if MIME type can't be determined
            mime_type = 'application/octet-stream'
        
        # Prepare file metadata
        file_metadata = {
            'name': os.path.basename(image_path)
        }
        
        # If folder_id is provided, set parent folder
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Upload the file
        media = MediaFileUpload(image_path, mimetype=mime_type, resumable=True)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,mimeType,webViewLink,webContentLink'
        ).execute()
        
        # Make the file public by default
        self.service.permissions().create(
            fileId=file['id'],
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()
        
        return file
    
    def get_file_link(self, file_id: str, link_type: str = 'view') -> str:
        """
        Get a shareable link for a file.
        
        Args:
            file_id: The Google Drive file ID
            link_type: Type of link to return ('view' or 'download')
            
        Returns:
            Shareable link to the file
        """
        # First, ensure the file is accessible by anyone with the link
        self.service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()
        
        # Get the file metadata with links
        file = self.service.files().get(
            fileId=file_id,
            fields='webViewLink,webContentLink'
        ).execute()
        
        if link_type == 'view':
            return file.get('webViewLink', '')
        elif link_type == 'download':
            return file.get('webContentLink', '')
        else:
            raise ValueError("link_type must be either 'view' or 'download'")
    
    def upload_images_batch(self, image_paths: List[str], folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Upload multiple images to Google Drive.
        
        Args:
            image_paths: List of paths to image files
            folder_id: Optional Google Drive folder ID to upload to
            
        Returns:
            List of dictionaries containing file metadata including ids and links
        """
        results = []
        for image_path in image_paths:
            try:
                file = self.upload_image(image_path, folder_id)
                # No need to set permissions here as upload_image now handles it
                results.append(file)
            except Exception as e:
                print(f"Error uploading {image_path}: {str(e)}")
        
        return results
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional parent folder ID
            
        Returns:
            Dictionary containing folder metadata including id
        """
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        folder = self.service.files().create(
            body=file_metadata,
            fields='id,name,webViewLink'
        ).execute()
        
        return folder
    
    def list_files(self, folder_id: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in Google Drive, optionally filtered by folder or query.
        
        Args:
            folder_id: Optional folder ID to list files from
            query: Optional query string (see Google Drive API documentation for syntax)
            
        Returns:
            List of file metadata dictionaries
        """
        q = []
        
        if folder_id:
            q.append(f"'{folder_id}' in parents")
        
        if query:
            q.append(query)
        
        query_string = " and ".join(q) if q else ""
        
        results = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=query_string,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, webViewLink, webContentLink)',
                pageToken=page_token
            ).execute()
            
            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
        
        return results
    
    def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: ID of the file to delete
        """
        self.service.files().delete(fileId=file_id).execute()
    
    def get_image_embed_html(self, file_id: str, width: int = 800, height: Optional[int] = None) -> str:
        """
        Get HTML code to embed an image in a webpage.
        
        Args:
            file_id: The Google Drive file ID
            width: Width of the image in pixels
            height: Optional height of the image in pixels
            
        Returns:
            HTML code to embed the image
        """
        # Ensure the file is publicly accessible
        self.service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()
        
        # Get direct image link
        # Note: This is a workaround as Google Drive doesn't provide direct embedding links
        # The format https://drive.google.com/uc?export=view&id=FILE_ID works for most images
        direct_link = f"https://drive.google.com/uc?export=view&id={file_id}"
        
        # Create HTML
        height_attr = f' height="{height}"' if height else ''
        html = f'<img src="{direct_link}" width="{width}"{height_attr} alt="Google Drive Image">'
        
        return html


# Example usage
def example_usage():
    # Initialize the client
    client = GoogleDriveClient('path/to/credentials.json')
    
    # Upload a single image
    uploaded_file = client.upload_image('path/to/image.jpg')
    print(f"Uploaded file ID: {uploaded_file['id']}")
    
    # Get a shareable link
    view_link = client.get_file_link(uploaded_file['id'], 'view')
    print(f"View link: {view_link}")
    
    download_link = client.get_file_link(uploaded_file['id'], 'download')
    print(f"Download link: {download_link}")
    
    # Create a folder
    folder = client.create_folder('My Images')
    print(f"Created folder: {folder['name']} with ID: {folder['id']}")
    
    # Upload multiple images to the folder
    image_paths = ['image1.jpg', 'image2.png', 'image3.gif']
    uploaded_files = client.upload_images_batch(image_paths, folder['id'])
    print(f"Uploaded {len(uploaded_files)} images to folder")
    
    # Get HTML for embedding an image
    embed_html = client.get_image_embed_html(uploaded_file['id'], width=600)
    print(f"Embed HTML: {embed_html}")


if __name__ == "__main__":
    # Uncomment to run the example
    # example_usage()
    pass