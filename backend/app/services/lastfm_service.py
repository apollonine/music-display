"""
Last.fm API Service

Fetches currently playing/recently played tracks from Last.fm.
Works with any music source that scrobbles to Last.fm (Spotify, Apple Music, Plex, etc.)
"""

import httpx
from typing import Optional
from ..config import get_settings
from ..models import TrackInfo, SourceType


class LastFmService:
    def __init__(self):
        self.settings = get_settings()
        self.api_url = "https://ws.audioscrobbler.com/2.0/"
    
    def is_configured(self) -> bool:
        return bool(self.settings.lastfm_api_key and self.settings.lastfm_username)
    
    async def get_current_track(self) -> Optional[TrackInfo]:
        """Get the currently playing or most recent track from Last.fm."""
        if not self.is_configured():
            return None
        
        params = {
            "method": "user.getrecenttracks",
            "user": self.settings.lastfm_username,
            "api_key": self.settings.lastfm_api_key,
            "format": "json",
            "limit": 1,
            "extended": 1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.api_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                tracks = data.get("recenttracks", {}).get("track", [])
                if not tracks:
                    return None
                
                track = tracks[0] if isinstance(tracks, list) else tracks
                
                # Check if currently playing
                is_playing = track.get("@attr", {}).get("nowplaying") == "true"
                
                # Get album art (largest available)
                images = track.get("image", [])
                album_art_url = None
                for img in reversed(images):
                    if img.get("#text"):
                        album_art_url = img["#text"]
                        break
                
                # Get artist info
                artist_name = track.get("artist", {}).get("name", "Unknown Artist")
                if isinstance(track.get("artist"), str):
                    artist_name = track["artist"]
                
                track_info = TrackInfo(
                    id=track.get("mbid") or f"lastfm_{track.get('name', 'unknown')}",
                    title=track.get("name", "Unknown Track"),
                    artist=artist_name,
                    album=track.get("album", {}).get("#text", "Unknown Album"),
                    album_art_url=album_art_url,
                    is_playing=is_playing,
                    source=SourceType.SPOTIFY,  # Last.fm doesn't tell us the actual source
                    duration_ms=0,
                    progress_ms=0,
                )
                
                # Try to get additional artist info
                artist_info = await self._get_artist_info(artist_name)
                if artist_info:
                    track_info.artist_image_url = artist_info.get("image")
                    track_info.genre = artist_info.get("tags", [])[:3]
                    track_info.artist_bio = artist_info.get("bio")
                
                # Try to get track info for duration
                track_details = await self._get_track_info(artist_name, track.get("name", ""))
                if track_details:
                    track_info.duration_ms = track_details.get("duration", 0)
                
                return track_info
                
            except Exception as e:
                print(f"Last.fm API error: {e}")
                return None
    
    async def _get_artist_info(self, artist: str) -> Optional[dict]:
        """Get artist details from Last.fm."""
        params = {
            "method": "artist.getinfo",
            "artist": artist,
            "api_key": self.settings.lastfm_api_key,
            "format": "json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.api_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                artist_data = data.get("artist", {})
                
                # Get largest image
                images = artist_data.get("image", [])
                image_url = None
                for img in reversed(images):
                    if img.get("#text"):
                        image_url = img["#text"]
                        break
                
                # Get tags/genres
                tags = [tag["name"] for tag in artist_data.get("tags", {}).get("tag", [])]
                
                # Get bio summary
                bio = artist_data.get("bio", {}).get("summary", "")
                # Clean up bio (remove HTML links)
                if bio:
                    import re
                    bio = re.sub(r'<a href=".*?">.*?</a>', '', bio).strip()
                
                return {
                    "image": image_url,
                    "tags": tags,
                    "bio": bio[:500] if bio else None
                }
            except Exception:
                return None
    
    async def _get_track_info(self, artist: str, track: str) -> Optional[dict]:
        """Get track details from Last.fm."""
        params = {
            "method": "track.getinfo",
            "artist": artist,
            "track": track,
            "api_key": self.settings.lastfm_api_key,
            "format": "json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.api_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                track_data = data.get("track", {})
                duration = int(track_data.get("duration", 0))
                
                return {"duration": duration}
            except Exception:
                return None


lastfm_service = LastFmService()
