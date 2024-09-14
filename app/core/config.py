from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GOOGLE_SHEETS_CREDENTIALS_FILE: str
    SHEET_ID: str

    class Config:
        env_file = ".env"

settings = Settings()