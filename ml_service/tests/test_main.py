import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import create_app
from app.settings import Settings


def make_settings(**kwargs) -> Settings:
    defaults = dict(
        prometheus_url="http://test:9090",
        worker_interval_seconds=3600,
    )
    defaults.update(kwargs)
    return Settings(**defaults)


def make_mock_http_client() -> MagicMock:
    """
    Мок httpx.AsyncClient — все HTTP-вызовы мгновенно возвращают
    пустой ответ Prometheus, воркер не зависает на реальной сети.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": {"result": []}}

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock()
    mock_client.aclose = AsyncMock()

    return mock_client


def test_create_app():
    """Приложение создаётся без ошибок, заголовок совпадает."""
    app = create_app(make_settings())
    assert app is not None
    assert app.title == "Server Failure Prediction Service"


def test_app_lifespan_healthz():
    """
    После старта lifespan /healthz отвечает 200.
    Патчим httpx.AsyncClient чтобы воркер не делал реальных запросов.
    """
    app = create_app(make_settings())

    with patch("app.main.httpx.AsyncClient", return_value=make_mock_http_client()):
        with TestClient(app) as client:
            response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lifespan_creates_analysis_service():
    """
    После входа в lifespan app.state.analysis_service существует и не None.
    """
    app = create_app(make_settings())

    with patch("app.main.httpx.AsyncClient", return_value=make_mock_http_client()):
        with TestClient(app) as client:
            assert hasattr(app.state, "analysis_service")
            assert app.state.analysis_service is not None