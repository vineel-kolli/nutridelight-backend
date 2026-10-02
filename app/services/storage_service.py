from urllib.parse import urlparse

from supabase import Client, create_client

from app.core.config import settings


PRIZE_IMAGE_BUCKET = "prize-images"


supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)


def upload_prize_image(
    *,
    file_data: bytes,
    path: str,
    content_type: str,
) -> str:
    supabase.storage.from_(
        PRIZE_IMAGE_BUCKET
    ).upload(
        path=path,
        file=file_data,
        file_options={
            "content-type": content_type,
            "cache-control": "3600",
            "upsert": "false",
        },
    )

    return supabase.storage.from_(
        PRIZE_IMAGE_BUCKET
    ).get_public_url(path)


def get_prize_image_storage_path(
    image_url: str | None,
) -> str | None:
    if not image_url:
        return None

    parsed_url = urlparse(image_url)

    expected_prefix = (
        f"/storage/v1/object/public/"
        f"{PRIZE_IMAGE_BUCKET}/"
    )

    if not parsed_url.path.startswith(
        expected_prefix
    ):
        return None

    storage_path = parsed_url.path[
        len(expected_prefix):
    ]

    if not storage_path:
        return None

    return storage_path


def delete_prize_image(
    *,
    path: str,
) -> None:
    supabase.storage.from_(
        PRIZE_IMAGE_BUCKET
    ).remove(
        [path]
    )