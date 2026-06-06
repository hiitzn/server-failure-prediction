import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI

from app.api.router import router
from app.detector import AnalysisService, IsolationForestDetector, SigmaDetector
from app.prometheus import AGENT_METRICS, PrometheusClient
from app.settings import Settings
from app.worker import AnalysisWorker


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Application factory.

    Accepting optional settings makes the function easy to use in tests
    with overridden config (e.g. a mock Prometheus URL).
    """
    if settings is None:
        settings = Settings()

    _configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # ── startup ──────────────────────────────────────────────────────────
        http_client = httpx.AsyncClient()
        prometheus = PrometheusClient(settings.prometheus_url, http_client)

        detectors = [
            SigmaDetector(
                threshold=settings.sigma_threshold,
                min_points=settings.min_data_points,
            ),
            IsolationForestDetector(
                contamination=settings.iforest_contamination,
                min_points=settings.min_data_points * 2,
            ),
        ]

        analysis_service = AnalysisService(
            prometheus=prometheus,
            detectors=detectors,
            metrics=AGENT_METRICS,
            lookback_seconds=settings.lookback_seconds,
        )

        # Store on app.state so the API router can retrieve it.
        app.state.analysis_service = analysis_service

        worker = AnalysisWorker(analysis_service, settings.worker_interval_seconds)
        worker_task = asyncio.create_task(worker.run())

        yield

        # ── shutdown ─────────────────────────────────────────────────────────
        worker_task.cancel()
        await asyncio.gather(worker_task, return_exceptions=True)
        await http_client.aclose()

    app = FastAPI(
        title="Server Failure Prediction Service",
        description="Detects anomalies in server metrics using 3σ and Isolation Forest.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


def _configure_logging(level: str) -> None:
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "root": {"level": level, "handlers": ["console"]},
    })
