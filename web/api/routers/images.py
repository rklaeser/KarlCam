"""
Image serving endpoints for KarlCam Fog API

This module provides endpoints for accessing camera images stored in Cloud Storage.
"""
from fastapi import APIRouter, Depends, Path
from fastapi.responses import RedirectResponse

from ..services.image_service import ImageService
from ..core.dependencies import get_storage_client, get_bucket_name

router = APIRouter(
    tags=["Images"],
    responses={
        404: {
            "description": "Image not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Image file not found",
                        "error_code": "IMAGE_NOT_FOUND",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cloud Storage access failed",
                        "error_code": "STORAGE_ERROR",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)


@router.get(
    "/images/{filename}",
    summary="Access camera image by filename",
    description="""
    Provides access to camera images stored in Google Cloud Storage by redirecting
    to the direct storage URL.
    
    This endpoint serves as a proxy to access camera images while maintaining
    consistent API access patterns. Instead of serving the image directly
    (which would double bandwidth usage), it returns a redirect to the
    Cloud Storage URL.
    
    ## Image Filename Format
    
    Images are stored with the filename pattern: `{camera_id}_{timestamp}.jpg`
    
    Examples:
    * `golden-gate-north_2024-01-10T08-30-00Z.jpg`
    * `alcatraz-view_2024-01-10T08-25-00Z.jpg`
    
    ## Performance Benefits
    
    * **Bandwidth Optimization**: Direct redirect eliminates double data transfer
    * **CDN Acceleration**: Cloud Storage provides global CDN distribution
    * **Caching**: Images are cached with 1-hour TTL for faster subsequent access
    * **Scalability**: Reduces load on API servers for image serving
    
    ## Response Behavior
    
    Returns a **302 redirect** to the direct Cloud Storage URL, allowing
    clients to access the image directly from Google's infrastructure.
    
    ## Use Cases
    
    * Displaying camera images in web applications
    * Downloading images for analysis or archival
    * Integrating with image processing workflows
    * Building gallery or timeline views of camera data
    """,
    response_description="Redirect to direct Cloud Storage image URL",
    responses={
        302: {
            "description": "Redirect to direct image URL in Cloud Storage",
            "headers": {
                "Location": {
                    "description": "Direct URL to the image in Cloud Storage",
                    "schema": {"type": "string"},
                    "example": "https://storage.googleapis.com/karlcam-fog-data/raw_images/golden-gate-north_2024-01-10T08-30-00Z.jpg"
                },
                "Cache-Control": {
                    "description": "Caching directive for the redirect",
                    "schema": {"type": "string"},
                    "example": "public, max-age=3600"
                }
            }
        }
    }
)
async def serve_image(
    filename: str = Path(
        ...,
        description="Image filename including camera ID and timestamp",
        example="golden-gate-north_2024-01-10T08-30-00Z.jpg"
    ),
    storage_client=Depends(get_storage_client),
    bucket_name: str = Depends(get_bucket_name)
):
    """Redirect to direct Cloud Storage image URL"""
    service = ImageService(storage_client, bucket_name)
    direct_url = service.get_image_url(filename)
    
    # Redirect to direct GCS URL to eliminate bandwidth doubling
    return RedirectResponse(
        url=direct_url,
        status_code=302,
        headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
    )