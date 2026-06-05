from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All runtime settings are read from environment variables.
    Defaults are safe for local docker-compose usage.
    """

    prometheus_url: str = Field(
        default="http://prometheus:9090",
        description="Base URL of the Prometheus HTTP API.",
    )

    # How many seconds of history to pull on each analysis run.
    lookback_seconds: int = Field(
        default=3600,
        description="Length of the time window sent to the detector (seconds).",
    )

    # How often the background worker runs a full analysis cycle.
    worker_interval_seconds: int = Field(
        default=60,
        description="Interval between background analysis runs (seconds).",
    )

    # Minimum data points required before the detector makes a decision.
    min_data_points: int = Field(
        default=10,
        description="Detector refuses to predict with fewer points than this.",
    )

    # Z-score threshold for the sigma detector.
    sigma_threshold: float = Field(
        default=3.0,
        description="Number of standard deviations that triggers a 3σ alert.",
    )

    # Contamination parameter for Isolation Forest (expected anomaly fraction).
    iforest_contamination: float = Field(
        default=0.05,
        description="Expected fraction of anomalies for Isolation Forest.",
    )

    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
