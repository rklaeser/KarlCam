"""
Image service containing business logic for image operations
"""
import logging
from google.cloud import storage
from fastapi import HTTPException
from ..utils.exceptions import ImageNotFoundException, CloudStorageError

logger = logging.getLogger(__name__)


class ImageService:
    """Service class for image-related operations"""
    
    def __init__(self, storage_client: storage.Client, bucket_name: str):
        self.storage_client = storage_client
        self.bucket_name = bucket_name
    
    def get_image_url(self, filename: str) -> str:
        """Get direct Cloud Storage URL for image
        
        Returns:
            str: Direct GCS URL
        """
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"raw_images/{filename}")
            
            if not blob.exists():
                raise ImageNotFoundException(filename)
            
            # Return direct public GCS URL
            direct_url = f"https://storage.googleapis.com/{self.bucket_name}/raw_images/{filename}"
            return direct_url
            
        except ImageNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting image URL {filename}: {e}")
            raise CloudStorageError(f"Failed to get image URL for {filename}")