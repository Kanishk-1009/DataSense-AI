"""
FastAPI integration / smoke tests.

Verifies the real HTTP contract described in the API documentation WITHOUT
requiring Ollama: the deterministic endpoints (/, /health, /upload, /eda)
must work against live multipart uploads.

Agent endpoints (/analyze/*, /evaluate) intentionally require Ollama and are
NOT exercised here — they are covered by the mocked unit tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app

DATASETS = Path(__file__).resolve().parents[2] / "datasets"

client = TestClient(app)


# ---- Helpers ---------------------------------------------------------------

def _upload(name: str, **kwargs) -> "httpx.Response":
    return client.post(
        "/upload",
        files={"file": (name, open(DATASETS / name, "rb").read(), "text/csv")},
        **kwargs,
    )


# ---- GET endpoints ---------------------------------------------------------

class TestRoot:
    def test_root_ok(self):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "running"
        assert "message" in body

    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}

    def test_openapi_docs_available(self):
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert b"swagger" in resp.content.lower()


# ---- POST /upload ----------------------------------------------------------

class TestUpload:
    def test_upload_iris(self):
        resp = _upload("iris.csv")
        assert resp.status_code == 200
        body = resp.json()
        assert body["dataset_info"]["columns"] == 5
        assert body["dataset_info"]["rows"] == 150
        assert len(body["columns"]) == 5

    def test_upload_rejects_invalid_extension(self):
        resp = client.post(
            "/upload",
            files={"file": ("notes.txt", b"col\n1\n", "text/plain")},
        )
        assert resp.status_code == 400
        assert "CSV" in resp.json()["detail"]

    def test_upload_rejects_empty_csv(self):
        resp = client.post(
            "/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_upload_rejects_no_rows(self):
        resp = client.post(
            "/upload",
            files={"file": ("header_only.csv", b"a,b,c\n", "text/csv")},
        )
        assert resp.status_code == 400


# ---- POST /eda -------------------------------------------------------------

class TestEda:
    @pytest.mark.parametrize("name", ["iris.csv", "titanic.csv", "wine.csv"])
    def test_eda_completes_without_ollama(self, name):
        resp = client.post("/eda", files={"file": (name, open(DATASETS / name, "rb").read(), "text/csv")})
        assert resp.status_code == 200
        body = resp.json()
        expected_keys = {
            "numeric_statistics",
            "correlation_analysis",
            "outliers",
            "missingness",
            "target_analysis",
            "quality_score",
            "insights",
            "feature_summary",
            "ml_task",
            "ml_recommendation",
            "preprocessing",
            "feature_importance",
            "report",
        }
        assert expected_keys.issubset(body.keys())
        assert body["quality_score"]["score"] >= 0.0

    def test_eda_with_target(self):
        resp = client.post(
            "/eda",
            files={"file": ("iris.csv", open(DATASETS / "iris.csv", "rb").read(), "text/csv")},
            data={"target": "species"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["target_analysis"]["column"] == "species"
        assert body["ml_task"]["task"] == "classification"

    def test_eda_rejects_invalid_extension(self):
        resp = client.post(
            "/eda",
            files={"file": ("bad.txt", b"a\n1\n", "text/plain")},
        )
        assert resp.status_code == 400


# ---- CORS ------------------------------------------------------------------

class TestCors:
    def test_preflight_allows_origins(self):
        resp = client.options(
            "/eda",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "*"