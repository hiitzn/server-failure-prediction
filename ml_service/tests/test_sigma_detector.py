from datetime import datetime, timezone

import pytest

from app.detector.sigma import SigmaDetector
from app.models import DetectorKind, MetricPoint


def make_points(values: list[float]) -> list[MetricPoint]:
    """Helper: turn a list of floats into MetricPoint objects."""
    return [
        MetricPoint(
            timestamp=datetime.fromtimestamp(i, tz=timezone.utc),
            value=v,
        )
        for i, v in enumerate(values)
    ]


class TestSigmaDetector:
    def setup_method(self) -> None:
        self.detector = SigmaDetector(threshold=3.0, min_points=5)

    def test_no_anomaly_on_stable_series(self) -> None:
        points = make_points([50.0] * 20)
        result = self.detector.detect("cpu", points)

        assert result.is_anomaly is False
        assert result.detector == DetectorKind.SIGMA

    def test_detects_spike(self) -> None:
        # 19 normal values then one extreme spike.
        normal = [50.0] * 19
        spike = [200.0]
        points = make_points(normal + spike)

        result = self.detector.detect("cpu", points)

        assert result.is_anomaly is True
        assert result.score > 3.0

    def test_insufficient_data_returns_no_anomaly(self) -> None:
        points = make_points([80.0, 82.0, 79.0])  # fewer than min_points=5
        result = self.detector.detect("cpu", points)

        assert result.is_anomaly is False
        assert "not enough data" in result.detail

    def test_zero_std_does_not_raise(self) -> None:
        # All identical values → std=0, must not divide by zero.
        points = make_points([42.0] * 20)
        result = self.detector.detect("cpu", points)

        assert result.is_anomaly is False

    def test_result_carries_metric_name(self) -> None:
        points = make_points([10.0] * 10)
        result = self.detector.detect("disk", points)

        assert result.metric_name == "disk"

    @pytest.mark.parametrize("threshold", [1.0, 2.0, 5.0])
    def test_custom_threshold(self, threshold: float) -> None:
        detector = SigmaDetector(threshold=threshold, min_points=5)
        # Mean=50, std≈0, last value=51 → z≈0, never anomaly regardless of threshold.
        points = make_points([50.0] * 19 + [51.0])
        result = detector.detect("mem", points)

        # z ≈ 0.19 — below even threshold=1.0.
        assert result.is_anomaly is False
