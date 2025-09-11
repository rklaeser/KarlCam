"""
Custom exceptions for KarlCam API
"""
from fastapi import HTTPException
from typing import Any, Dict, Optional


class KarlCamException(HTTPException):
    """Base exception for KarlCam API"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, headers)
        self.error_code = error_code


class CameraNotFoundException(KarlCamException):
    """Exception raised when a camera is not found"""
    def __init__(self, camera_id: str):
        super().__init__(
            status_code=404,
            detail=f"Camera with id {camera_id} not found",
            error_code="CAMERA_NOT_FOUND"
        )


class DatabaseConnectionError(KarlCamException):
    """Exception raised when database connection fails"""
    def __init__(self, detail: str = "Unable to connect to database"):
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="DATABASE_CONNECTION_ERROR"
        )


class ImageNotFoundException(KarlCamException):
    """Exception raised when an image is not found"""
    def __init__(self, image_id: str):
        super().__init__(
            status_code=404,
            detail=f"Image {image_id} not found",
            error_code="IMAGE_NOT_FOUND"
        )


class NoImagesFoundError(KarlCamException):
    """Exception raised when no images are found for a camera"""
    def __init__(self, camera_id: str):
        super().__init__(
            status_code=404,
            detail=f"No collected images found for camera {camera_id}",
            error_code="NO_IMAGES_FOUND"
        )


class InvalidRequestError(KarlCamException):
    """Exception raised for invalid requests"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="INVALID_REQUEST"
        )


class DataProcessingError(KarlCamException):
    """Exception raised when data processing fails"""
    def __init__(self, detail: str = "Failed to process data"):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="PROCESSING_ERROR"
        )


class CloudStorageError(KarlCamException):
    """Exception raised when Cloud Storage operations fail"""
    def __init__(self, detail: str = "Cloud Storage operation failed"):
        super().__init__(
            status_code=502,
            detail=detail,
            error_code="CLOUD_STORAGE_ERROR"
        )