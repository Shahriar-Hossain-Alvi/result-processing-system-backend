import cloudinary
import cloudinary.uploader
from loguru import logger
from app.core import settings
from fastapi import HTTPException, status

# Cloudinary Configuration
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def delete_image_from_cloudinary(public_id: str):

    try:
        if not public_id:
            return None
        result = cloudinary.uploader.destroy(public_id)
        logger.success(f"Image deleted from Cloudinary: {public_id}")
        return result
    except Exception as e:
        logger.error(f"Error deleting image from Cloudinary: {e}")
        return None
