from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_dry_run: bool = True
    booking_dry_run: bool = True
    app_url: str = "http://localhost:8000"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./quiz_master.db"
    organizer_name: str = "Miriam KI Tool"
    organizer_email: str = "miriam.wassmann@adesso.de"
    organizer_phone: str = "017696830342"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
