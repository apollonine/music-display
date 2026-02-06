import httpx
from typing import Optional
import asyncio


class LyricsService:
    """
    Fetches lyrics from various sources.
    Uses lyrics.ovh as primary source (free, no API key required).
    """
    
    def __init__(self):
        self.lyrics_ovh_url = "https://api.lyrics.ovh/v1"
    
    async def get_lyrics(self, artist: str, title: str) -> Optional[str]:
        """
        Fetch lyrics for a given artist and song title.
        """
        # Clean up title (remove featuring artists, remix info, etc.)
        clean_title = self._clean_title(title)
        clean_artist = self._clean_artist(artist)
        
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.lyrics_ovh_url}/{clean_artist}/{clean_title}"
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    lyrics = data.get("lyrics")
                    if lyrics:
                        return self._format_lyrics(lyrics)
                
                return None
                
            except Exception as e:
                print(f"Lyrics fetch error: {e}")
                return None
    
    def _clean_title(self, title: str) -> str:
        """Remove common suffixes that interfere with lyrics search."""
        import re
        # Remove text in parentheses or brackets
        title = re.sub(r'\s*[\(\[].*?[\)\]]', '', title)
        # Remove "- Remastered", "- Live", etc.
        title = re.sub(r'\s*-\s*(Remastered|Live|Radio Edit|Single Version).*$', '', title, flags=re.IGNORECASE)
        return title.strip()
    
    def _clean_artist(self, artist: str) -> str:
        """Clean artist name for search."""
        # Take only first artist if multiple
        if "," in artist:
            artist = artist.split(",")[0]
        if " & " in artist:
            artist = artist.split(" & ")[0]
        if " feat" in artist.lower():
            artist = artist.lower().split(" feat")[0]
        return artist.strip()
    
    def _format_lyrics(self, lyrics: str) -> str:
        """Format lyrics for display."""
        # Remove excessive blank lines
        lines = lyrics.split('\n')
        formatted_lines = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            formatted_lines.append(line)
            prev_blank = is_blank
        
        return '\n'.join(formatted_lines).strip()


lyrics_service = LyricsService()
