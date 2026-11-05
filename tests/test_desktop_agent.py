from fastapi.testclient import TestClient

from desktop_agent.config import AgentSettings
from desktop_agent.service import create_app


def settings(token="test-token", allowed_apps=None):
    return AgentSettings(
        host="127.0.0.1",
        port=8765,
        token=token,
        cors_origins=("http://localhost:5173",),
        allowed_apps=allowed_apps or {"editor": ["notepad.exe"]},
        max_capture_width=1920,
    )


def test_health_is_public_and_does_not_expose_token():
    with TestClient(create_app(settings())) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "token" not in response.text.lower()


def test_apps_requires_bearer_token():
    with TestClient(create_app(settings())) as client:
        assert client.get("/v1/apps").status_code == 401
        assert client.get("/v1/apps", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.get("/v1/apps", headers={"Authorization": "Bearer test-token"}).status_code == 200


def test_unlisted_app_is_rejected_without_launching_process():
    with TestClient(create_app(settings())) as client:
        response = client.post(
            "/v1/apps/open",
            headers={"Authorization": "Bearer test-token"},
            json={"app": "powershell"},
        )
    assert response.status_code == 403


def test_missing_token_configuration_fails_closed():
    with TestClient(create_app(settings(token=""))) as client:
        response = client.get("/v1/apps")
    assert response.status_code == 503
