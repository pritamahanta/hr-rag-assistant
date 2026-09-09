from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch
from app.services.query import QueryServiceError



client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_rejects_whitespace_question():
    response = client.post(
        "/query",
        json={"question": "   "},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Question must not be empty."
    }


def test_list_documents_endpoint():
    response = client.get("/documents/")

    assert response.status_code == 200
    assert "documents" in response.json()


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "image.png",
                b"not a policy",
                "image/png",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Unsupported file type. Allowed types: .md, .txt, .pdf"
        )
    }


def test_query_returns_500_when_query_service_fails():
    with patch(
        "app.routes.query.answer_query",
        side_effect=QueryServiceError("Retrieval failed."),
    ):
        response = client.post(
            "/query",
            json={"question": "How many casual leave days?"},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "The query service is temporarily unavailable. Please try again."
    )