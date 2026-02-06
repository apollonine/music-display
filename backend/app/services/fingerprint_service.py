import asyncio
import subprocess
import tempfile
import os
from typing import Optional, Tuple
import httpx

from ..config import get_settings
from ..models import TrackInfo, SourceType


class FingerprintService:
    """
    Audio fingerprinting service using AcoustID/Chromaprint.
    Used for identifying music from analog sources (vinyl, tape, CD).
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.acoustid_url = "https://api.acoustid.org/v2/lookup"
        self.musicbrainz_url = "https://musicbrainz.org/ws/2"
    
    async def identify_from_audio(self, audio_data: bytes, sample_rate: int = 44100) -> Optional[TrackInfo]:
        """
        Identify a track from raw audio data using AcoustID.
        """
        # Save audio to temp file for fpcalc processing
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            fingerprint, duration = await self._generate_fingerprint(temp_path)
            if not fingerprint:
                return None
            
            return await self._lookup_fingerprint(fingerprint, duration)
        finally:
            os.unlink(temp_path)
    
    async def identify_from_file(self, file_path: str) -> Optional[TrackInfo]:
        """
        Identify a track from an audio file.
        """
        fingerprint, duration = await self._generate_fingerprint(file_path)
        if not fingerprint:
            return None
        
        return await self._lookup_fingerprint(fingerprint, duration)
    
    async def _generate_fingerprint(self, file_path: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Generate audio fingerprint using fpcalc (Chromaprint).
        """
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["fpcalc", "-json", file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            )
            
            if result.returncode != 0:
                print(f"fpcalc error: {result.stderr}")
                return None, None
            
            import json
            data = json.loads(result.stdout)
            return data.get("fingerprint"), int(data.get("duration", 0))
            
        except FileNotFoundError:
            print("fpcalc not found. Install chromaprint: brew install chromaprint")
            return None, None
        except Exception as e:
            print(f"Fingerprint generation error: {e}")
            return None, None
    
    async def _lookup_fingerprint(self, fingerprint: str, duration: int) -> Optional[TrackInfo]:
        """
        Look up fingerprint in AcoustID database.
        """
        if not self.settings.acoustid_api_key:
            print("AcoustID API key not configured")
            return None
        
        params = {
            "client": self.settings.acoustid_api_key,
            "fingerprint": fingerprint,
            "duration": duration,
            "meta": "recordings releasegroups"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.acoustid_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "ok" or not data.get("results"):
                    return None
                
                # Get best match
                best_result = max(data["results"], key=lambda x: x.get("score", 0))
                
                if best_result.get("score", 0) < 0.5:
                    return None
                
                recordings = best_result.get("recordings", [])
                if not recordings:
                    return None
                
                recording = recordings[0]
                release_groups = recording.get("releasegroups", [])
                
                track_info = TrackInfo(
                    id=recording.get("id", "unknown"),
                    title=recording.get("title", "Unknown Track"),
                    artist=recording.get("artists", [{}])[0].get("name", "Unknown Artist") if recording.get("artists") else "Unknown Artist",
                    album=release_groups[0].get("title", "Unknown Album") if release_groups else "Unknown Album",
                    source=SourceType.ANALOG,
                    is_playing=True
                )
                
                # Try to get album art from MusicBrainz/Cover Art Archive
                if release_groups:
                    release_group_id = release_groups[0].get("id")
                    if release_group_id:
                        track_info.album_art_url = f"https://coverartarchive.org/release-group/{release_group_id}/front-500"
                
                return track_info
                
            except Exception as e:
                print(f"AcoustID lookup error: {e}")
                return None


fingerprint_service = FingerprintService()
