"""
Image serving endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from ..services.image_service import ImageService
from ..core.dependencies import get_storage_client, get_bucket_name

router = APIRouter(tags=["images"])


@router.get("/images/{filename}")
async def serve_image(
    filename: str,
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