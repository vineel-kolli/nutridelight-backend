from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

FRONTEND_ORIGIN = "http://localhost:5173"
EVIL_ORIGIN = "http://evil.example"


def test_cors_allows_configured_frontend_origin():
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_unknown_origin():
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": EVIL_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_configured_methods():
    for method in ["GET", "POST", "PUT", "DELETE"]:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Access-Control-Request-Method": method,
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


def test_cors_does_not_allow_wildcard_origin():
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] != "*"