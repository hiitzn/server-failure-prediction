from datetime import datetime, timezone

from app.detector.isolation_forest import IsolationForestDetector
from app.models import DetectorKind, MetricPoint


def make_points(values: list[float]) -> list[MetricPoint]:
    return [
        MetricPoint(
            timestamp=datetime.fromtimestamp(i, tz=timezone.utc),
            value=v,
        )
        for i, v in enumerate(values)
    ]


class TestIsolationForestDetector:
    def setup_method(self) -> None:
        self.detector = IsolationForestDetector(contamination=0.05, min_points=20)

    def test_stable_series_not_anomalous(self) -> None:
        points = make_points([50.0 + i % 3 for i in range(60)])
        result = self.detector.detect("cpu", points)

        assert result.detector == DetectorKind.ISOLATION_FOREST
        # Stable series should NOT be flagged.
        assert result.is_anomaly is False

    def test_extreme_outlier_detected(self) -> None:
        # 59 normal points, then one extreme value.
        points = make_points([50.0] * 59 + [999.0])
        result = self.detector.detect("cpu", points)

        assert result.is_anomaly is True

    def test_insufficient_data_returns_no_anomaly(self) -> None:
        points = make_points([80.0] * 10)  # fewer than min_points=20
        result = self.detector.detect("cpu", points)

        assert result.is_anomaly is False
        assert "not enough data" in result.detail

    def test_score_is_finite_float(self) -> None:
        points = make_points([30.0 + i % 5 for i in range(50)])
        result = self.detector.detect("mem", points)

        assert isinstance(result.score, float)
        assert result.score == result.score  # NaN check

    def test_invalid_contamination_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError):
            IsolationForestDetector(contamination=0.0)
        with pytest.raises(ValueError):
            IsolationForestDetector(contamination=0.5)
