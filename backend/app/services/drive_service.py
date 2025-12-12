"""Google Drive service for fetching files"""
import os
import io
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from app.core import get_logger

logger = get_logger(__name__)


class DriveService:
    """Service for interacting with Google Drive"""
    
    def __init__(self, folder_id: str):
        self.folder_id = folder_id
        self.service = None
        
    def initialize(self):
        """Initialize Drive service with default credentials"""
        try:
            # Use Application Default Credentials (works with Cloud Run service account)
            from google.auth import default
            credentials, project = default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            return False
    
    def download_file_by_name(self, filename: str, destination_path: str) -> bool:
        """
        Download a file from Drive folder by filename
        
        Args:
            filename: Name of the file to download (e.g., 'tax_code.pdf')
            destination_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Search for file in folder
            query = f"'{self.folder_id}' in parents and name='{filename}' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                logger.error(f"File '{filename}' not found in Drive folder")
                return False
            
            file_id = files[0]['id']
            logger.info(f"Found file '{filename}' with ID: {file_id}")
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            with open(destination_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Download {int(status.progress() * 100)}%")
            
            logger.info(f"File downloaded successfully to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file from Drive: {e}")
            return False
