from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.json()['ok'] is True


def test_missing_job_returns_404_with_error_contract():
    resp = client.get('/api/v1/jobs/not-found')
    assert resp.status_code == 404
    assert resp.json()['code'] == 'JOB_NOT_FOUND'


def test_models_endpoint():
    resp = client.get('/api/v1/models')
    assert resp.status_code == 200
    payload = resp.json()
    assert payload['default'] in {'tiny', 'base', 'small', 'medium', 'large'}
    assert len(payload['options']) >= 1


def test_create_job_rejects_invalid_model():
    resp = client.post('/api/v1/jobs', data={'model_size': 'bad-size'})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_MODEL_SIZE'
