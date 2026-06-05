from app.prometheus.client import PrometheusClient


class TestPrometheusClientParse:
    """
    Tests for the static _parse method only.
    HTTP calls are tested via integration tests (not required for block 2).
    """

    def test_parses_valid_payload(self) -> None:
        payload = {
            "data": {
                "result": [
                    {
                        "values": [
                            [1_700_000_000.0, "42.5"],
                            [1_700_000_015.0, "43.1"],
                        ]
                    }
                ]
            }
        }
        points = PrometheusClient._parse(payload)

        assert len(points) == 2
        assert points[0].value == 42.5
        assert points[1].value == 43.1
        # Results must be sorted by timestamp.
        assert points[0].timestamp < points[1].timestamp

    def test_empty_result_returns_empty_list(self) -> None:
        payload = {"data": {"result": []}}
        assert PrometheusClient._parse(payload) == []

    def test_missing_data_key_returns_empty_list(self) -> None:
        assert PrometheusClient._parse({}) == []

    def test_malformed_value_is_skipped(self) -> None:
        payload = {
            "data": {
                "result": [
                    {
                        "values": [
                            [1_700_000_000.0, "not_a_number"],
                            [1_700_000_015.0, "55.0"],
                        ]
                    }
                ]
            }
        }
        points = PrometheusClient._parse(payload)
        # Only the valid point survives.
        assert len(points) == 1
        assert points[0].value == 55.0
