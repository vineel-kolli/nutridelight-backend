from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.api.dependencies import (
    get_current_admin,
    require_admin_origin,
)
from app.models.admin_user import AdminUser
from app.services.storage_service import upload_prize_image


router = APIRouter(
    prefix="/admin/uploads",
    tags=["Admin Uploads"],
)


MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@router.post("/prize-image")
async def upload_prize_image_endpoint(
    file: UploadFile = File(...),
    _: AdminUser = Depends(get_current_admin),
    __: None = Depends(require_admin_origin),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Image file is required",
        )

    extension = ALLOWED_IMAGE_TYPES.get(
        file.content_type or ""
    )

    if extension is None:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WebP images are allowed",
        )

    file_data = await file.read(
        MAX_IMAGE_SIZE + 1
    )

    if len(file_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image must be 5 MB or smaller",
        )

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty",
        )

    try:
        with Image.open(BytesIO(file_data)) as image:
            image.verify()
    except (
        UnidentifiedImageError,
        OSError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image",
        ) from exc

    generated_filename = (
        f"{uuid4().hex}{extension}"
    )

    storage_path = (
        f"prizes/{generated_filename}"
    )

    image_url = upload_prize_image(
        file_data=file_data,
        path=storage_path,
        content_type=file.content_type
        or "application/octet-stream",
    )

    return {
        "url": image_url,
        "filename": generated_filename,
    }