import asyncio
import logging

from app.detector.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class AnalysisWorker:
    """
    Runs AnalysisService on a fixed interval in the background.

    The worker is started via asyncio and respects asyncio cancellation:
    when the app shuts down, the current sleep is interrupted cleanly.
    """

    def __init__(self, service: AnalysisService, interval_seconds: int) -> None:
        self._service = service
        self._interval = interval_seconds

    async def run(self) -> None:
        """
        Loop forever: analyse → sleep → repeat.
        Exits gracefully when the task is cancelled.
        """
        logger.info("analysis worker started (interval=%ds)", self._interval)

        while True:
            await self._run_once()
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                logger.info("analysis worker stopped")
                return

    async def _run_once(self) -> None:
        try:
            results = await self._service.run()
            anomalies = [r for r in results if r.is_anomaly]
            logger.info(
                "analysis cycle complete: %d results, %d anomalies",
                len(results),
                len(anomalies),
            )
        except Exception as exc:
            # Never let a single cycle crash the worker.
            logger.error("analysis cycle failed: %s", exc, exc_info=True)
