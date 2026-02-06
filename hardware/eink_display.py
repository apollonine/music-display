"""
E-Ink Display Driver

Renders album art and track info on a Waveshare e-ink display.
Optimized for slow refresh - only updates when track changes.
"""

import io
import asyncio
from dataclasses import dataclass
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Try to import e-ink library (only works on Raspberry Pi)
try:
    from waveshare_epd import epd7in5_V2
    EINK_AVAILABLE = True
except ImportError:
    EINK_AVAILABLE = False
    print("E-ink library not available - running in simulation mode")


@dataclass
class DisplayConfig:
    width: int = 800
    height: int = 480
    album_art_size: int = 300
    font_title_size: int = 36
    font_artist_size: int = 28
    font_album_size: int = 22


class EinkDisplay:
    def __init__(self, config: DisplayConfig = None):
        self.config = config or DisplayConfig()
        self.epd = None
        self.current_track_id: Optional[str] = None
        self._font_title = None
        self._font_artist = None
        self._font_album = None
        self._load_fonts()
    
    def _load_fonts(self):
        """Load fonts for text rendering."""
        try:
            self._font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.config.font_title_size)
            self._font_artist = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.config.font_artist_size)
            self._font_album = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.config.font_album_size)
        except OSError:
            self._font_title = ImageFont.load_default()
            self._font_artist = ImageFont.load_default()
            self._font_album = ImageFont.load_default()
    
    def init(self):
        """Initialize the e-ink display."""
        if EINK_AVAILABLE:
            self.epd = epd7in5_V2.EPD()
            self.epd.init()
            self.epd.Clear()
            print("E-ink display initialized")
        else:
            print("E-ink simulation mode - images will be saved to disk")
    
    def clear(self):
        """Clear the display."""
        if self.epd:
            self.epd.Clear()
    
    def sleep(self):
        """Put display to sleep to save power."""
        if self.epd:
            self.epd.sleep()
    
    async def update_track(self, track_info: dict) -> bool:
        """
        Update display with new track info.
        Returns True if display was updated, False if skipped (same track).
        """
        track_id = track_info.get('id')
        
        if track_id == self.current_track_id:
            return False
        
        self.current_track_id = track_id
        
        image = await self._render_track(track_info)
        
        if self.epd:
            self.epd.display(self.epd.getbuffer(image))
        else:
            image.save("/tmp/eink_preview.png")
            print(f"E-ink preview saved: /tmp/eink_preview.png")
        
        return True
    
    async def _render_track(self, track_info: dict) -> Image.Image:
        """Render track info to an image."""
        image = Image.new('L', (self.config.width, self.config.height), 255)
        draw = ImageDraw.Draw(image)
        
        album_art = await self._get_album_art(track_info.get('album_art_url'))
        
        if album_art:
            album_art = album_art.convert('L')
            album_art = ImageOps.autocontrast(album_art)
            album_art = album_art.resize(
                (self.config.album_art_size, self.config.album_art_size),
                Image.Resampling.LANCZOS
            )
            
            album_art = album_art.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
            album_art = album_art.convert('L')
            
            art_x = 40
            art_y = (self.config.height - self.config.album_art_size) // 2
            image.paste(album_art, (art_x, art_y))
        
        text_x = self.config.album_art_size + 80
        text_width = self.config.width - text_x - 40
        
        title = track_info.get('title', 'Unknown Track')
        title = self._truncate_text(title, self._font_title, text_width)
        title_y = 140
        draw.text((text_x, title_y), title, font=self._font_title, fill=0)
        
        artist = track_info.get('artist', 'Unknown Artist')
        artist = self._truncate_text(artist, self._font_artist, text_width)
        artist_y = title_y + 50
        draw.text((text_x, artist_y), artist, font=self._font_artist, fill=60)
        
        album = track_info.get('album', 'Unknown Album')
        album = self._truncate_text(album, self._font_album, text_width)
        album_y = artist_y + 40
        draw.text((text_x, album_y), album, font=self._font_album, fill=100)
        
        line_y = album_y + 50
        draw.line([(text_x, line_y), (self.config.width - 40, line_y)], fill=180, width=1)
        
        source = track_info.get('source', 'unknown')
        source_text = f":: {source.upper()}"
        source_y = line_y + 20
        draw.text((text_x, source_y), source_text, font=self._font_album, fill=120)
        
        return image
    
    async def _get_album_art(self, url: Optional[str]) -> Optional[Image.Image]:
        """Download album art from URL."""
        if not url:
            return None
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Failed to download album art: {e}")
            return None
    
    def _truncate_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """Truncate text to fit within max_width."""
        if not text:
            return ""
        
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0] if bbox else 0
        
        if text_width <= max_width:
            return text
        
        while text and text_width > max_width:
            text = text[:-1]
            bbox = font.getbbox(text + "...")
            text_width = bbox[2] - bbox[0] if bbox else 0
        
        return text + "..."


eink_display = EinkDisplay()


async def main():
    """Test the e-ink display with sample data."""
    display = EinkDisplay()
    display.init()
    
    sample_track = {
        'id': 'test_1',
        'title': 'Bohemian Rhapsody',
        'artist': 'Queen',
        'album': 'A Night at the Opera',
        'album_art_url': 'https://i.scdn.co/image/ab67616d0000b273ce4f1737bc8a646c8c4bd25a',
        'source': 'shazam'
    }
    
    await display.update_track(sample_track)
    print("Display updated!")


if __name__ == "__main__":
    asyncio.run(main())
