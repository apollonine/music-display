from pydantic import BaseModel
from typing import Optional
from enum import Enum


class SourceType(str, Enum):
    SPOTIFY = "spotify"
    ANALOG = "analog"
    UNKNOWN = "unknown"


class TrackInfo(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    album_art_url: Optional[str] = None
    album_art_colors: Optional[list[str]] = None
    duration_ms: int = 0
    progress_ms: int = 0
    is_playing: bool = False
    source: SourceType = SourceType.UNKNOWN
    
    # Extended metadata
    release_year: Optional[int] = None
    genre: Optional[list[str]] = None
    lyrics: Optional[str] = None
    artist_image_url: Optional[str] = None
    artist_bio: Optional[str] = None


class DisplayMode(str, Enum):
    ALBUM_ART = "album_art"
    LYRICS = "lyrics"
    ARTIST_INFO = "artist_info"
    VISUALIZER = "visualizer"
    MINIMAL = "minimal"


class DisplayState(BaseModel):
    mode: DisplayMode = DisplayMode.ALBUM_ART
    brightness: int = 100
    track: Optional[TrackInfo] = None


class ControlEvent(BaseModel):
    type: str  # "rotate", "press", "long_press", "touch"
    value: Optional[int] = None  # For rotation: direction (-1, 1)
    x: Optional[int] = None  # For touch
    y: Optional[int] = None
