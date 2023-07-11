from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cost:cost@localhost:5432/cost"
    redis_url: str = "redis://localhost:6379"
    alert_webhook_url: str = ""

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    # GCP
    gcp_project_id: str = ""
    google_application_credentials: str = ""

    # Azure
    azure_subscription_id: str = ""
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # anomaly detection — flag spend > mean + (z_threshold * stddev)
    anomaly_z_threshold: float = 2.0
    baseline_days: int = 30


settings = Settings()
