from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.api.dependencies import (
    get_current_admin,
    require_admin_origin,
)
from app.models.admin_user import AdminUser


router = APIRouter(
    prefix="/admin/uploads",
    tags=["Admin Uploads"],
)


UPLOAD_ROOT = Path("uploads")
PRIZE_UPLOAD_DIR = UPLOAD_ROOT / "prizes"

MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@router.post("/prize-image")
async def upload_prize_image(
    request: Request,
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

    PRIZE_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_filename = (
        f"{uuid4().hex}{extension}"
    )

    destination = (
        PRIZE_UPLOAD_DIR / generated_filename
    )

    destination.write_bytes(file_data)

    relative_url = (
        f"/uploads/prizes/{generated_filename}"
    )

    base_url = str(
        request.base_url
    ).rstrip("/")

    return {
        "url": f"{base_url}{relative_url}",
        "filename": generated_filename,
    }