"""
Custom exceptions for KarlCam Fog API
"""
from fastapi import HTTPException


class CameraNotFoundError(HTTPException):
    """Exception raised when a camera is not found"""
    
    def __init__(self, camera_id: str):
        super().__init__(
            status_code=404,
            detail=f"Camera {camera_id} not found"
        )


class ImageNotFoundError(HTTPException):
    """Exception raised when an image is not found"""
    
    def __init__(self, filename: str):
        super().__init__(
            status_code=404,
            detail=f"Image {filename} not found"
        )


class NoImagesFoundError(HTTPException):
    """Exception raised when no images are found for a camera"""
    
    def __init__(self, camera_id: str):
        super().__init__(
            status_code=404,
            detail=f"No collected images found for camera {camera_id}"
        )


class DatabaseConnectionError(HTTPException):
    """Exception raised when database connection fails"""
    
    def __init__(self, detail: str = "Database connection failed"):
        super().__init__(
            status_code=500,
            detail=detail
        )


class CloudStorageError(HTTPException):
    """Exception raised when cloud storage operations fail"""
    
    def __init__(self, detail: str = "Cloud storage operation failed"):
        super().__init__(
            status_code=500,
            detail=detail
        )