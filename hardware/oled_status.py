"""
OLED Status Display Driver

Shows real-time playback status on a small OLED display.
Updates frequently (every second) for progress bar and play state.
"""

import time
from dataclasses import dataclass
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# Try to import OLED library (only works on Raspberry Pi)
try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print("OLED library not available - running in simulation mode")


@dataclass
class OLEDConfig:
    width: int = 128
    height: int = 64
    i2c_port: int = 1
    i2c_address: int = 0x3C


class OLEDStatus:
    def __init__(self, config: OLEDConfig = None):
        self.config = config or OLEDConfig()
        self.device = None
        self._font_time = None
        self._font_small = None
        self._load_fonts()
        
        self.current_track_id: Optional[str] = None
        self.duration_ms: int = 0
        self.progress_ms: int = 0
        self.is_playing: bool = False
        self.last_update_time: float = 0
    
    def _load_fonts(self):
        """Load fonts for text rendering."""
        try:
            self._font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self._font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except OSError:
            self._font_time = ImageFont.load_default()
            self._font_small = ImageFont.load_default()
    
    def init(self):
        """Initialize the OLED display."""
        if OLED_AVAILABLE:
            serial = i2c(port=self.config.i2c_port, address=self.config.i2c_address)
            self.device = ssd1306(serial, width=self.config.width, height=self.config.height)
            print("OLED display initialized")
        else:
            print("OLED simulation mode")
    
    def update_track(self, track_info: dict):
        """Update track info (called when track changes)."""
        self.current_track_id = track_info.get('id')
        self.duration_ms = track_info.get('duration_ms', 0)
        self.progress_ms = track_info.get('progress_ms', 0)
        self.is_playing = track_info.get('is_playing', False)
        self.last_update_time = time.time()
        self.render()
    
    def update_progress(self, progress_ms: int, is_playing: bool):
        """Update progress (called frequently)."""
        self.progress_ms = progress_ms
        self.is_playing = is_playing
        self.last_update_time = time.time()
        self.render()
    
    def tick(self):
        """Called every second to update progress if playing."""
        if self.is_playing and self.duration_ms > 0:
            elapsed = time.time() - self.last_update_time
            self.progress_ms += int(elapsed * 1000)
            self.progress_ms = min(self.progress_ms, self.duration_ms)
            self.last_update_time = time.time()
            self.render()
    
    def render(self):
        """Render the current state to the display."""
        image = Image.new('1', (self.config.width, self.config.height), 0)
        draw = ImageDraw.Draw(image)
        
        # Play/pause icon
        icon_x = 5
        icon_y = 22
        if self.is_playing:
            # Play triangle
            draw.polygon([(icon_x, icon_y), (icon_x, icon_y + 20), (icon_x + 15, icon_y + 10)], fill=1)
        else:
            # Pause bars
            draw.rectangle([icon_x, icon_y, icon_x + 5, icon_y + 20], fill=1)
            draw.rectangle([icon_x + 10, icon_y, icon_x + 15, icon_y + 20], fill=1)
        
        # Current time
        current_time = self._format_time(self.progress_ms)
        draw.text((25, 24), current_time, font=self._font_time, fill=1)
        
        # Total time
        total_time = self._format_time(self.duration_ms)
        total_width = self._font_time.getbbox(total_time)[2]
        draw.text((self.config.width - total_width - 5, 24), total_time, font=self._font_time, fill=1)
        
        # Progress bar
        bar_x = 5
        bar_y = 50
        bar_width = self.config.width - 10
        bar_height = 8
        
        # Bar background
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], outline=1, fill=0)
        
        # Bar fill
        if self.duration_ms > 0:
            progress_ratio = self.progress_ms / self.duration_ms
            fill_width = int(bar_width * progress_ratio)
            if fill_width > 0:
                draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], fill=1)
            
            # Progress dot
            dot_x = bar_x + fill_width
            dot_y = bar_y + bar_height // 2
            draw.ellipse([dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4], fill=1)
        
        # Display or save
        if self.device:
            self.device.display(image)
        else:
            image.save("/tmp/oled_preview.png")
    
    def _format_time(self, ms: int) -> str:
        """Format milliseconds as M:SS."""
        if ms <= 0:
            return "0:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def clear(self):
        """Clear the display."""
        if self.device:
            self.device.clear()
    
    def sleep(self):
        """Turn off the display."""
        if self.device:
            self.device.hide()


oled_status = OLEDStatus()


def main():
    """Test the OLED display."""
    display = OLEDStatus()
    display.init()
    
    display.update_track({
        'id': 'test_1',
        'duration_ms': 354000,
        'progress_ms': 120000,
        'is_playing': True
    })
    
    print("OLED preview saved to /tmp/oled_preview.png")
    
    # Simulate playback
    for _ in range(10):
        time.sleep(1)
        display.tick()
        print(f"Progress: {display.progress_ms // 1000}s")


if __name__ == "__main__":
    main()
