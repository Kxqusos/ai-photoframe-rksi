from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Photoframe API"


settings = Settings()
