import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, Optional
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Cloudinary manually to avoid validation issues
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

if all([cloud_name, api_key, api_secret]):
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/avi", "video/mov", "video/wmv"
}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

async def upload_media(file: UploadFile, folder: str = "jansamadhan/complaints") -> Dict[str, Any]:
    """
    Upload media file to Cloudinary
    
    Args:
        file: UploadFile object from FastAPI
        folder: Cloudinary folder path
        
    Returns:
        Dict containing url, public_id, and type
        
    Raises:
        HTTPException: If file validation fails or upload fails
    """
    try:
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Validate file type
        content_type = file.content_type or ""
        if not (content_type in ALLOWED_IMAGE_TYPES or 
                content_type in ALLOWED_VIDEO_TYPES or 
                content_type in ALLOWED_DOCUMENT_TYPES):
            raise HTTPException(
                status_code=400,
                detail=f"File type {content_type} not allowed. Allowed types: images, videos, PDFs"
            )
        
        # Determine resource type
        resource_type = "auto"
        upload_params = {
            "resource_type": "auto",
            "type": "upload",
            "folder": folder,
            "use_filename": True,
            "unique_filename": True,
            "overwrite": True
        }

        if content_type in ALLOWED_IMAGE_TYPES:
            resource_type = "image"
            upload_params["resource_type"] = "image"
            upload_params["format"] = "auto"
        elif content_type in ALLOWED_VIDEO_TYPES:
            resource_type = "video"
            upload_params["resource_type"] = "video"
        elif content_type in ALLOWED_DOCUMENT_TYPES:
            # Use raw for documents to ensure they are served as-is (fix for PDF issues)
            resource_type = "raw"
            upload_params["resource_type"] = "raw"
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file.file, **upload_params)
        
        return {
            "url": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id"),
            "type": upload_result.get("resource_type"),
            "format": upload_result.get("format"),
            "size_bytes": upload_result.get("bytes", file_size),
            "original_filename": file.filename,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

async def delete_media(public_id: str) -> bool:
    """
    Delete media from Cloudinary
    
    Args:
        public_id: Cloudinary public ID
        
    Returns:
        bool: True if deletion successful
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Failed to delete media {public_id}: {str(e)}")
        return False

async def get_media_info(public_id: str) -> Optional[Dict[str, Any]]:
    """
    Get media information from Cloudinary
    
    Args:
        public_id: Cloudinary public ID
        
    Returns:
        Dict with media info or None if not found
    """
    try:
        result = cloudinary.api.resource(public_id)
        return {
            "public_id": result.get("public_id"),
            "url": result.get("secure_url"),
            "type": result.get("resource_type"),
            "format": result.get("format"),
            "size_bytes": result.get("bytes"),
            "created_at": result.get("created_at")
        }
    except Exception as e:
        print(f"Failed to get media info {public_id}: {str(e)}")
        return None

def validate_media_file(file: UploadFile) -> Dict[str, Any]:
    """
    Validate media file before upload
    
    Args:
        file: UploadFile object
        
    Returns:
        Dict with validation results
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        validation_result["valid"] = False
        validation_result["errors"].append(
            f"File size {file_size // (1024*1024)}MB exceeds limit of {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Check file type
    content_type = file.content_type or ""
    if not (content_type in ALLOWED_IMAGE_TYPES or 
            content_type in ALLOWED_VIDEO_TYPES or 
            content_type in ALLOWED_DOCUMENT_TYPES):
        validation_result["valid"] = False
        validation_result["errors"].append(
            f"File type {content_type} not allowed"
        )
    
    # Add warnings for large files
    if file_size > 5 * 1024 * 1024:  # 5MB
        validation_result["warnings"].append(
            "Large file may take longer to upload and process"
        )
    
    return validation_result
