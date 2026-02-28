import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.auth import enable_no_auth_docs, apply_cors

def test_enable_no_auth_docs_no_auth():
    app = FastAPI(docs_url=None, redoc_url=None)
    enable_no_auth_docs(app, no_auth=True)
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200
    response = client.get("/redoc")
    assert response.status_code == 200

def test_enable_no_auth_docs_auth():
    app = FastAPI(docs_url=None, redoc_url=None)
    enable_no_auth_docs(app, no_auth=False)
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 404
    response = client.get("/redoc")
    assert response.status_code == 404
