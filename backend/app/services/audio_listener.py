"""
Audio Listener Service

Captures audio from microphone and identifies tracks using Shazam.
Ideal for vinyl, tape, CD, or any analog audio source.
"""

import asyncio
import tempfile
import os
import wave
import struct
from typing import Optional, Callable
from dataclasses import dataclass

from ..config import get_settings
from ..models import TrackInfo, SourceType

# Try to import pyaudio, but don't fail if not available
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("PyAudio not available - microphone listening disabled")

# Try to import shazamio
try:
    from shazamio import Shazam
    SHAZAM_AVAILABLE = True
except ImportError:
    SHAZAM_AVAILABLE = False
    print("ShazamIO not available - install with: pip install shazamio")


@dataclass
class ListenerConfig:
    sample_rate: int = 44100
    channels: int = 1
    chunk_size: int = 1024
    record_seconds: int = 10  # How long to record for fingerprinting
    silence_threshold: int = 100  # RMS threshold for silence detection (lowered for sensitivity)


class AudioListener:
    def __init__(self, config: ListenerConfig = None):
        self.config = config or ListenerConfig()
        self.settings = get_settings()
        self.is_listening = False
        self._audio = None
        self._stream = None
        self._on_track_identified: Optional[Callable] = None
    
    def is_available(self) -> bool:
        """Check if audio listening is available."""
        return PYAUDIO_AVAILABLE and SHAZAM_AVAILABLE
    
    def set_callback(self, callback: Callable[[TrackInfo], None]):
        """Set callback for when a track is identified."""
        self._on_track_identified = callback
    
    async def start_listening(self):
        """Start continuous audio listening."""
        if not self.is_available():
            print("Audio listener not available (missing PyAudio or AcoustID API key)")
            return
        
        self.is_listening = True
        print("Starting audio listener... (recording 10s samples)")
        
        while self.is_listening:
            try:
                # Record audio sample
                print("[Audio] Recording...")
                audio_data = await self._record_sample()
                
                if audio_data:
                    has_audio = self._has_audio_content(audio_data)
                    print(f"[Audio] Recorded {len(audio_data)} bytes, has audio: {has_audio}")
                    
                    if has_audio:
                        # Identify the track using Shazam
                        print("[Audio] Identifying track with Shazam...")
                        track = await self._identify_with_shazam(audio_data)
                        
                        if track:
                            print(f"[Audio] Identified: {track.title} by {track.artist}")
                            if self._on_track_identified:
                                await self._on_track_identified(track)
                        else:
                            print("[Audio] No match found")
                
                # Wait before next sample
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Audio listener error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)
    
    def stop_listening(self):
        """Stop audio listening."""
        self.is_listening = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._audio:
            self._audio.terminate()
    
    async def _record_sample(self) -> Optional[bytes]:
        """Record audio sample from microphone."""
        if not PYAUDIO_AVAILABLE:
            return None
        
        loop = asyncio.get_event_loop()
        
        def record():
            audio = pyaudio.PyAudio()
            
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=self.config.channels,
                    rate=self.config.sample_rate,
                    input=True,
                    frames_per_buffer=self.config.chunk_size
                )
                
                frames = []
                num_chunks = int(self.config.sample_rate / self.config.chunk_size * self.config.record_seconds)
                
                for _ in range(num_chunks):
                    data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
                return b''.join(frames)
                
            finally:
                audio.terminate()
        
        try:
            return await loop.run_in_executor(None, record)
        except Exception as e:
            print(f"Recording error: {e}")
            return None
    
    def _has_audio_content(self, audio_data: bytes) -> bool:
        """Check if audio data contains actual sound (not silence)."""
        # Calculate RMS of audio
        count = len(audio_data) // 2
        shorts = struct.unpack(f"{count}h", audio_data)
        
        sum_squares = sum(s * s for s in shorts)
        rms = (sum_squares / count) ** 0.5
        
        return rms > self.config.silence_threshold
    
    async def _identify_with_shazam(self, audio_data: bytes) -> Optional[TrackInfo]:
        """Identify audio using Shazam."""
        if not SHAZAM_AVAILABLE:
            return None
        
        # Save to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            
            with wave.open(f.name, 'wb') as wav:
                wav.setnchannels(self.config.channels)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(self.config.sample_rate)
                wav.writeframes(audio_data)
        
        try:
            shazam = Shazam()
            result = await shazam.recognize(temp_path)
            
            if not result or 'track' not in result:
                print(f"[Audio] Shazam: No track in response")
                return None
            
            track_data = result['track']
            
            # Get album art
            album_art_url = None
            if 'images' in track_data:
                album_art_url = track_data['images'].get('coverarthq') or track_data['images'].get('coverart')
            
            # Get genre
            genres = []
            try:
                if 'genres' in track_data:
                    genre_data = track_data.get('genres', {})
                    if isinstance(genre_data, dict):
                        genres = [g.get('primary', '') for g in genre_data.values() if isinstance(g, dict) and g.get('primary')]
                    elif isinstance(genre_data, str):
                        genres = [genre_data]
            except Exception:
                pass
            
            return TrackInfo(
                id=track_data.get('key', 'shazam_unknown'),
                title=track_data.get('title', 'Unknown Track'),
                artist=track_data.get('subtitle', 'Unknown Artist'),
                album=track_data.get('sections', [{}])[0].get('metadata', [{}])[0].get('text', 'Unknown Album') if track_data.get('sections') else 'Unknown Album',
                album_art_url=album_art_url,
                source=SourceType.ANALOG,
                is_playing=True,
                duration_ms=0,
                progress_ms=0,
                genre=genres,
            )
            
        except Exception as e:
            print(f"[Audio] Shazam error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            os.unlink(temp_path)
    
    async def _identify_audio(self, audio_data: bytes) -> Optional[TrackInfo]:
        """Identify audio using AcoustID."""
        # Save to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            
            # Write WAV file
            with wave.open(f.name, 'wb') as wav:
                wav.setnchannels(self.config.channels)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(self.config.sample_rate)
                wav.writeframes(audio_data)
        
        try:
            # Generate fingerprint using fpcalc
            fingerprint, duration = await self._generate_fingerprint(temp_path)
            
            if not fingerprint:
                return None
            
            # Look up in AcoustID
            return await self._lookup_acoustid(fingerprint, duration)
            
        finally:
            os.unlink(temp_path)
    
    async def _generate_fingerprint(self, file_path: str) -> tuple:
        """Generate audio fingerprint using fpcalc."""
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
                print(f"[Audio] fpcalc error: {result.stderr}")
                return None, None
            
            import json
            data = json.loads(result.stdout)
            fingerprint = data.get("fingerprint")
            duration = int(data.get("duration", 0))
            print(f"[Audio] Fingerprint generated: duration={duration}s, fp_len={len(fingerprint) if fingerprint else 0}")
            return fingerprint, duration
            
        except FileNotFoundError:
            print("fpcalc not found. Install chromaprint: brew install chromaprint")
            return None, None
        except Exception as e:
            print(f"Fingerprint error: {e}")
            return None, None
    
    async def _lookup_acoustid(self, fingerprint: str, duration: int) -> Optional[TrackInfo]:
        """Look up fingerprint in AcoustID database."""
        import httpx
        
        params = {
            "client": self.settings.acoustid_api_key,
            "fingerprint": fingerprint,
            "duration": duration,
            "meta": "recordings releasegroups"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.acoustid.org/v2/lookup",
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                print(f"[Audio] AcoustID response: status={data.get('status')}, results={len(data.get('results', []))}")
                
                if data.get("status") != "ok" or not data.get("results"):
                    return None
                
                # Get best match
                best = max(data["results"], key=lambda x: x.get("score", 0))
                
                if best.get("score", 0) < 0.5:
                    return None
                
                recordings = best.get("recordings", [])
                if not recordings:
                    return None
                
                rec = recordings[0]
                release_groups = rec.get("releasegroups", [])
                
                # Get album art from Cover Art Archive
                album_art_url = None
                if release_groups:
                    rg_id = release_groups[0].get("id")
                    if rg_id:
                        album_art_url = f"https://coverartarchive.org/release-group/{rg_id}/front-500"
                
                artists = rec.get("artists", [])
                artist_name = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
                
                return TrackInfo(
                    id=rec.get("id", "unknown"),
                    title=rec.get("title", "Unknown Track"),
                    artist=artist_name,
                    album=release_groups[0].get("title", "Unknown Album") if release_groups else "Unknown Album",
                    album_art_url=album_art_url,
                    source=SourceType.ANALOG,
                    is_playing=True,
                    duration_ms=duration * 1000,
                    progress_ms=0,
                )
                
            except Exception as e:
                print(f"AcoustID lookup error: {e}")
                return None


audio_listener = AudioListener()
