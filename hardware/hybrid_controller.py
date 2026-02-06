"""
Hybrid Display Controller

Coordinates between e-ink (album art) and OLED (status) displays.
Connects to the backend via WebSocket for real-time updates.
"""

import asyncio
import json
import signal
import sys
from typing import Optional

try:
    import websockets
except ImportError:
    print("websockets not installed. Run: pip install websockets")
    sys.exit(1)

from eink_display import eink_display
from oled_status import oled_status


class HybridController:
    def __init__(self, backend_url: str = "ws://localhost:8000/ws"):
        self.backend_url = backend_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.current_track: Optional[dict] = None
    
    async def start(self):
        """Start the hybrid display controller."""
        self.running = True
        
        # Initialize displays
        print("Initializing displays...")
        eink_display.init()
        oled_status.init()
        
        # Start background tasks
        await asyncio.gather(
            self._connect_websocket(),
            self._oled_tick_loop()
        )
    
    async def stop(self):
        """Stop the controller and clean up."""
        self.running = False
        
        if self.ws:
            await self.ws.close()
        
        eink_display.sleep()
        oled_status.sleep()
        print("Displays put to sleep")
    
    async def _connect_websocket(self):
        """Connect to backend and handle messages."""
        reconnect_delay = 1
        
        while self.running:
            try:
                print(f"Connecting to {self.backend_url}...")
                async with websockets.connect(self.backend_url) as ws:
                    self.ws = ws
                    reconnect_delay = 1
                    print("Connected to backend")
                    
                    async for message in ws:
                        await self._handle_message(message)
                        
            except websockets.ConnectionClosed:
                print("Connection closed")
            except Exception as e:
                print(f"WebSocket error: {e}")
            
            if self.running:
                print(f"Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 30)
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'track_update':
                track = data.get('track')
                if track:
                    self.current_track = track
                    
                    # Update e-ink (only if track changed)
                    updated = await eink_display.update_track(track)
                    if updated:
                        print(f"E-ink updated: {track.get('title')} by {track.get('artist')}")
                    
                    # Update OLED
                    oled_status.update_track(track)
                    
            elif msg_type == 'progress_update':
                progress_ms = data.get('progress_ms', 0)
                is_playing = data.get('is_playing', False)
                oled_status.update_progress(progress_ms, is_playing)
                
            elif msg_type == 'mode_change':
                # Mode changes don't affect hardware displays
                pass
                
        except json.JSONDecodeError:
            print(f"Invalid JSON: {message}")
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def _oled_tick_loop(self):
        """Update OLED progress every second."""
        while self.running:
            await asyncio.sleep(1)
            if self.current_track:
                oled_status.tick()


async def main():
    """Main entry point."""
    controller = HybridController()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def shutdown():
        print("\nShutting down...")
        asyncio.create_task(controller.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)
    
    try:
        await controller.start()
    except KeyboardInterrupt:
        await controller.stop()


if __name__ == "__main__":
    print("=" * 50)
    print("  Hybrid Display Controller")
    print("  E-ink: Album Art + Track Info")
    print("  OLED: Progress Bar + Play State")
    print("=" * 50)
    asyncio.run(main())
