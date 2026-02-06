import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional
import asyncio
from functools import partial

from ..config import get_settings
from ..models import TrackInfo, SourceType


class SpotifyService:
    def __init__(self):
        settings = get_settings()
        self.sp: Optional[spotipy.Spotify] = None
        self.auth_manager: Optional[SpotifyOAuth] = None
        self._setup_auth(settings)
    
    def _setup_auth(self, settings):
        if settings.spotify_client_id and settings.spotify_client_secret:
            self.auth_manager = SpotifyOAuth(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
                redirect_uri=settings.spotify_redirect_uri,
                scope="user-read-playback-state user-read-currently-playing user-modify-playback-state",
                cache_path=".spotify_cache"
            )
    
    def get_auth_url(self) -> Optional[str]:
        if self.auth_manager:
            return self.auth_manager.get_authorize_url()
        return None
    
    def handle_callback(self, code: str) -> bool:
        if self.auth_manager:
            token_info = self.auth_manager.get_access_token(code)
            if token_info:
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                return True
        return False
    
    def is_authenticated(self) -> bool:
        if self.auth_manager:
            token_info = self.auth_manager.get_cached_token()
            if token_info:
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                return True
        return False
    
    async def get_current_track(self) -> Optional[TrackInfo]:
        if not self.sp:
            return None
        
        loop = asyncio.get_event_loop()
        try:
            current = await loop.run_in_executor(
                None, 
                self.sp.current_playback
            )
            
            if not current or not current.get("item"):
                return None
            
            item = current["item"]
            album = item.get("album", {})
            artists = item.get("artists", [])
            
            # Get largest album art
            images = album.get("images", [])
            album_art_url = images[0]["url"] if images else None
            
            # Get artist info
            artist_name = artists[0]["name"] if artists else "Unknown Artist"
            artist_id = artists[0]["id"] if artists else None
            
            track_info = TrackInfo(
                id=item["id"],
                title=item["name"],
                artist=artist_name,
                album=album.get("name", "Unknown Album"),
                album_art_url=album_art_url,
                duration_ms=item.get("duration_ms", 0),
                progress_ms=current.get("progress_ms", 0),
                is_playing=current.get("is_playing", False),
                source=SourceType.SPOTIFY,
                release_year=int(album.get("release_date", "0")[:4]) if album.get("release_date") else None
            )
            
            # Fetch artist image if available
            if artist_id:
                artist_info = await loop.run_in_executor(
                    None,
                    partial(self.sp.artist, artist_id)
                )
                if artist_info and artist_info.get("images"):
                    track_info.artist_image_url = artist_info["images"][0]["url"]
                if artist_info and artist_info.get("genres"):
                    track_info.genre = artist_info["genres"][:3]
            
            return track_info
            
        except Exception as e:
            print(f"Error fetching Spotify track: {e}")
            return None
    
    async def play_pause(self) -> bool:
        if not self.sp:
            return False
        loop = asyncio.get_event_loop()
        try:
            current = await loop.run_in_executor(None, self.sp.current_playback)
            if current and current.get("is_playing"):
                await loop.run_in_executor(None, self.sp.pause_playback)
            else:
                await loop.run_in_executor(None, self.sp.start_playback)
            return True
        except Exception as e:
            print(f"Error toggling playback: {e}")
            return False
    
    async def next_track(self) -> bool:
        if not self.sp:
            return False
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self.sp.next_track)
            return True
        except Exception as e:
            print(f"Error skipping track: {e}")
            return False
    
    async def previous_track(self) -> bool:
        if not self.sp:
            return False
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self.sp.previous_track)
            return True
        except Exception as e:
            print(f"Error going to previous track: {e}")
            return False


spotify_service = SpotifyService()
