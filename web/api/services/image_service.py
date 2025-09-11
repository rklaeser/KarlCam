"""
Image service containing business logic for image operations
"""
import logging
from google.cloud import storage
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ImageService:
    """Service class for image-related operations"""
    
    def __init__(self, storage_client: storage.Client, bucket_name: str):
        self.storage_client = storage_client
        self.bucket_name = bucket_name
    
    def serve_image(self, filename: str) -> tuple[bytes, str]:
        """Serve image from Cloud Storage
        
        Returns:
            tuple: (image_data, content_type)
        """
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"raw_images/{filename}")
            
            if not blob.exists():
                raise HTTPException(status_code=404, detail="Image not found")
            
            # Download the image data
            image_data = blob.download_as_bytes()
            
            # Determine content type based on file extension
            content_type = "image/jpeg"  # Default
            if filename.lower().endswith('.png'):
                content_type = "image/png"
            elif filename.lower().endswith('.gif'):
                content_type = "image/gif"
            elif filename.lower().endswith('.webp'):
                content_type = "image/webp"
            
            return image_data, content_type
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving image {filename}: {e}")
            raise HTTPException(status_code=500, detail="Failed to serve image")