from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Spotify
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/callback"
    
    # Last.fm
    lastfm_api_key: str = ""
    lastfm_username: str = ""
    
    # AcoustID
    acoustid_api_key: str = ""
    
    # Audio Listener
    enable_audio_listener: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
