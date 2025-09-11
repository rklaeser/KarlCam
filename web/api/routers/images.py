"""
Image serving endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import io

from ..services.image_service import ImageService
from ..core.dependencies import get_storage_client, get_bucket_name

router = APIRouter(tags=["images"])


@router.get("/images/{filename}")
async def serve_image(
    filename: str,
    storage_client=Depends(get_storage_client),
    bucket_name: str = Depends(get_bucket_name)
):
    """Serve image from Cloud Storage"""
    service = ImageService(storage_client, bucket_name)
    image_data, content_type = service.serve_image(filename)
    
    # Return the image data as a streaming response
    return StreamingResponse(
        io.BytesIO(image_data),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
    )