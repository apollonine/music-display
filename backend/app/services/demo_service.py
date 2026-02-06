import asyncio
import time
from typing import Optional
from ..models import TrackInfo, SourceType


DEMO_TRACKS = [
    TrackInfo(
        id="demo_1",
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        album_art_url="https://i.scdn.co/image/ab67616d0000b273ce4f1737bc8a646c8c4bd25a",
        duration_ms=354000,
        progress_ms=0,
        is_playing=True,
        source=SourceType.SPOTIFY,
        release_year=1975,
        genre=["rock", "classic rock"],
        lyrics="Is this the real life? Is this just fantasy?\nCaught in a landslide, no escape from reality\nOpen your eyes, look up to the skies and see\nI'm just a poor boy, I need no sympathy",
        artist_image_url="https://i.scdn.co/image/b1dfbe843b0b9f54ab2e588f33e7637d2dab065a",
    ),
    TrackInfo(
        id="demo_2",
        title="Hotel California",
        artist="Eagles",
        album="Hotel California",
        album_art_url="https://i.scdn.co/image/ab67616d0000b2734637341b9f507521afa9a778",
        duration_ms=391000,
        progress_ms=0,
        is_playing=True,
        source=SourceType.ANALOG,
        release_year=1977,
        genre=["rock", "soft rock"],
        lyrics="On a dark desert highway, cool wind in my hair\nWarm smell of colitas, rising up through the air\nUp ahead in the distance, I saw a shimmering light",
    ),
    TrackInfo(
        id="demo_3",
        title="Stairway to Heaven",
        artist="Led Zeppelin",
        album="Led Zeppelin IV",
        album_art_url="https://i.scdn.co/image/ab67616d0000b273c8a11e48c91a982d086afc69",
        duration_ms=482000,
        progress_ms=0,
        is_playing=True,
        source=SourceType.ANALOG,
        release_year=1971,
        genre=["rock", "hard rock"],
        lyrics="There's a lady who's sure all that glitters is gold\nAnd she's buying a stairway to heaven",
    ),
]


class DemoService:
    def __init__(self):
        self.current_track_index = 0
        self.start_time = time.time()
        self.is_playing = True
    
    def get_current_track(self) -> TrackInfo:
        track = DEMO_TRACKS[self.current_track_index].model_copy()
        
        if self.is_playing:
            elapsed = (time.time() - self.start_time) * 1000
            track.progress_ms = int(elapsed) % track.duration_ms
        
        track.is_playing = self.is_playing
        return track
    
    def next_track(self):
        self.current_track_index = (self.current_track_index + 1) % len(DEMO_TRACKS)
        self.start_time = time.time()
    
    def previous_track(self):
        self.current_track_index = (self.current_track_index - 1) % len(DEMO_TRACKS)
        self.start_time = time.time()
    
    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.start_time = time.time()


demo_service = DemoService()
