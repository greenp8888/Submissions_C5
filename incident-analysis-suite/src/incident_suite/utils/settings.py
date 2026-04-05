from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_name: str = "incident-suite"
    log_level: str = "INFO"
    api_base_url: str = "http://localhost:8000"
    auth_mode: str = "api_key"
    incident_api_key: str = ""

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_app_name: str = "incident-suite"
    openrouter_site_url: str = "http://localhost:8000"

    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_default_channel_id: str = ""
    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_redirect_uri: str = "http://localhost:8501"

    salesforce_auth_mode: str = "password"
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_domain: str = "login"
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_redirect_uri: str = "http://localhost:8501"
    salesforce_sandbox_domain: str = "test"
    salesforce_instance_url: str = ""
    salesforce_incident_object: str = "Case"

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "OPS"
    jira_issue_type: str = "Task"
    lancedb_path: str = ".incident_lancedb"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
