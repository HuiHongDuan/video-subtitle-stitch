from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthz():
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.json()['ok'] is True


def test_missing_job_returns_404():
    resp = client.get('/api/v1/jobs/not-found')
    assert resp.status_code == 404
