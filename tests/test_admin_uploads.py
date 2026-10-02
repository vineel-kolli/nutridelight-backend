from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.main import app
from app.models.admin_user import AdminUser
from app.services.auth_service import hash_password


client = TestClient(app,base_url="https://testserver",)


TEST_USERNAME = "uploadtestadmin"
TEST_PASSWORD = "TestPassword123!"
FRONTEND_ORIGIN = "http://localhost:5173"

def mock_prize_image_upload(monkeypatch):
    def fake_upload_prize_image(
        *,
        file_data: bytes,
        path: str,
        content_type: str,
    ) -> str:
        return (
            "https://test.supabase.co/"
            "storage/v1/object/public/"
            f"prize-images/{path}"
        )

    monkeypatch.setattr(
        "app.api.v1.admin_uploads.upload_prize_image",
        fake_upload_prize_image,
    )
def create_test_admin(db: Session) -> AdminUser:
    admin = AdminUser(
        username=TEST_USERNAME,
        password_hash=hash_password(TEST_PASSWORD),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    return admin


def create_test_image(image_format: str = "PNG") -> bytes:
    image = Image.new(
        "RGB",
        (100, 100),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format=image_format,
    )

    return buffer.getvalue()


def login_as_admin(db: Session) -> None:
    create_test_admin(db)

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def test_upload_requires_authentication(db):
    client.cookies.clear()

    image_data = create_test_image()

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "prize.png",
                image_data,
                "image/png",
            )
        },
    )

    assert response.status_code == 401


def test_upload_rejects_wrong_origin(db):
    client.cookies.clear()

    login_as_admin(db)

    image_data = create_test_image()

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": "http://evil.example",
        },
        files={
            "file": (
                "prize.png",
                image_data,
                "image/png",
            )
        },
    )

    assert response.status_code == 403


def test_upload_valid_png(db):
    client.cookies.clear()

    login_as_admin(db)

    image_data = create_test_image("PNG")

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "prize.png",
                image_data,
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["url"].startswith("https://")
    assert "/storage/v1/object/public/prize-images/prizes/" in data["url"]
    assert data["filename"].endswith(".png")


def test_upload_valid_jpeg(db):
    client.cookies.clear()

    login_as_admin(db)

    image_data = create_test_image("JPEG")

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "prize.jpg",
                image_data,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"].endswith(".jpg")


def test_upload_valid_webp(db):
    client.cookies.clear()

    login_as_admin(db)

    image_data = create_test_image("WEBP")

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "prize.webp",
                image_data,
                "image/webp",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"].endswith(".webp")


def test_upload_rejects_unsupported_mime_type(db):
    client.cookies.clear()

    login_as_admin(db)

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "prize.txt",
                b"not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only JPEG, PNG, and WebP images are allowed"
    )


def test_upload_rejects_fake_image(db):
    client.cookies.clear()

    login_as_admin(db)

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "fake.png",
                b"this is not actually an image",
                "image/png",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Uploaded file is not a valid image"
    )


def test_upload_rejects_empty_file(db):
    client.cookies.clear()

    login_as_admin(db)

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "empty.png",
                b"",
                "image/png",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Uploaded image is empty"
    )


def test_upload_rejects_file_larger_than_5_mb(db):
    client.cookies.clear()

    login_as_admin(db)

    oversized_data = b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "large.png",
                oversized_data,
                "image/png",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Image must be 5 MB or smaller"
    )


def test_upload_does_not_use_original_filename(db):
    client.cookies.clear()

    login_as_admin(db)

    image_data = create_test_image()

    response = client.post(
        "/api/v1/admin/uploads/prize-image",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        files={
            "file": (
                "../../malicious.png",
                image_data,
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    filename = data["filename"]

    assert "/" not in filename
    assert "\\" not in filename
    assert filename.endswith(".png")
    assert len(filename) == 36