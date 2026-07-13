import json
from typing import List, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    Uses Pydantic BaseSettings for strong typing and validation.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Supabase Configuration
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_key: str = Field(..., validation_alias="SUPABASE_KEY")

    # FastAPI Server Configuration
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # CORS Origins (Allowed Frontend URLs)
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        validation_alias="CORS_ORIGINS"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parses cors_origins into a list of strings if it was loaded as a string representation of a JSON list.
        """
        if isinstance(self.cors_origins, str):
            try:
                parsed = json.loads(self.cors_origins)
                if isinstance(parsed, list):
                    return [str(origin) for origin in parsed]
                return [self.cors_origins]
            except json.JSONDecodeError:
                # If it's not a valid JSON list, split by comma or return as a single element list
                if "," in self.cors_origins:
                    return [origin.strip() for origin in self.cors_origins.split(",")]
                return [self.cors_origins]
        return self.cors_origins


# Singleton instance of settings to be imported across the application
settings = Settings()
