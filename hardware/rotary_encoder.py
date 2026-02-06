"""
Rotary Encoder Controller for Music Display

This module handles physical rotary encoder input on Raspberry Pi GPIO.
It sends control events to the backend via WebSocket.

Hardware connections (example for KY-040 encoder):
- CLK -> GPIO 17
- DT  -> GPIO 18  
- SW  -> GPIO 27
- +   -> 3.3V
- GND -> GND
"""

import asyncio
import json
import websockets
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

# GPIO is only available on Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available - running in simulation mode")


class EventType(str, Enum):
    ROTATE = "rotate"
    PRESS = "press"
    LONG_PRESS = "long_press"


@dataclass
class ControlEvent:
    type: EventType
    value: Optional[int] = None  # -1 for CCW, 1 for CW


class RotaryEncoder:
    def __init__(
        self,
        clk_pin: int = 17,
        dt_pin: int = 18,
        sw_pin: int = 27,
        websocket_url: str = "ws://localhost:8000/ws"
    ):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.websocket_url = websocket_url
        
        self.last_clk_state = 0
        self.button_press_time = 0
        self.long_press_threshold = 0.5  # seconds
        
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        if GPIO_AVAILABLE:
            self._setup_gpio()
    
    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.last_clk_state = GPIO.input(self.clk_pin)
        
        # Set up interrupts
        GPIO.add_event_detect(
            self.clk_pin, 
            GPIO.BOTH, 
            callback=self._rotation_callback,
            bouncetime=5
        )
        GPIO.add_event_detect(
            self.sw_pin,
            GPIO.BOTH,
            callback=self._button_callback,
            bouncetime=50
        )
    
    def _rotation_callback(self, channel):
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state:
            if dt_state != clk_state:
                # Clockwise
                asyncio.run_coroutine_threadsafe(
                    self.event_queue.put(ControlEvent(EventType.ROTATE, 1)),
                    self.loop
                )
            else:
                # Counter-clockwise
                asyncio.run_coroutine_threadsafe(
                    self.event_queue.put(ControlEvent(EventType.ROTATE, -1)),
                    self.loop
                )
        
        self.last_clk_state = clk_state
    
    def _button_callback(self, channel):
        import time
        
        if GPIO.input(self.sw_pin) == GPIO.LOW:
            # Button pressed
            self.button_press_time = time.time()
        else:
            # Button released
            press_duration = time.time() - self.button_press_time
            
            if press_duration >= self.long_press_threshold:
                event = ControlEvent(EventType.LONG_PRESS)
            else:
                event = ControlEvent(EventType.PRESS)
            
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(event),
                self.loop
            )
    
    async def connect_websocket(self):
        while True:
            try:
                self.ws = await websockets.connect(self.websocket_url)
                print(f"Connected to {self.websocket_url}")
                return
            except Exception as e:
                print(f"WebSocket connection failed: {e}, retrying in 2s...")
                await asyncio.sleep(2)
    
    async def send_event(self, event: ControlEvent):
        if self.ws:
            try:
                message = {
                    "type": "control",
                    "data": {
                        "type": event.type.value,
                        "value": event.value
                    }
                }
                await self.ws.send(json.dumps(message))
                print(f"Sent: {event}")
            except Exception as e:
                print(f"Failed to send event: {e}")
                await self.connect_websocket()
    
    async def event_processor(self):
        while True:
            event = await self.event_queue.get()
            await self.send_event(event)
    
    async def run(self):
        self.loop = asyncio.get_event_loop()
        
        await self.connect_websocket()
        
        # Start event processor
        processor_task = asyncio.create_task(self.event_processor())
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            processor_task.cancel()
            if self.ws:
                await self.ws.close()
            if GPIO_AVAILABLE:
                GPIO.cleanup()


class SimulatedEncoder:
    """
    Simulated encoder for development/testing without hardware.
    Uses keyboard input instead of GPIO.
    """
    
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws"):
        self.websocket_url = websocket_url
        self.ws = None
    
    async def connect_websocket(self):
        while True:
            try:
                self.ws = await websockets.connect(self.websocket_url)
                print(f"Connected to {self.websocket_url}")
                return
            except Exception as e:
                print(f"WebSocket connection failed: {e}, retrying in 2s...")
                await asyncio.sleep(2)
    
    async def send_event(self, event: ControlEvent):
        if self.ws:
            message = {
                "type": "control",
                "data": {
                    "type": event.type.value,
                    "value": event.value
                }
            }
            await self.ws.send(json.dumps(message))
            print(f"Sent: {event}")
    
    async def run(self):
        await self.connect_websocket()
        
        print("\nSimulated Encoder Controls:")
        print("  Left Arrow  - Rotate CCW (previous mode)")
        print("  Right Arrow - Rotate CW (next mode)")
        print("  Space       - Button press (play/pause)")
        print("  Enter       - Long press (next track)")
        print("  Ctrl+C      - Exit\n")
        
        import sys
        import tty
        import termios
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            
            while True:
                ch = sys.stdin.read(1)
                
                if ch == '\x03':  # Ctrl+C
                    break
                elif ch == '\x1b':  # Escape sequence
                    ch2 = sys.stdin.read(1)
                    ch3 = sys.stdin.read(1)
                    if ch2 == '[':
                        if ch3 == 'D':  # Left arrow
                            await self.send_event(ControlEvent(EventType.ROTATE, -1))
                        elif ch3 == 'C':  # Right arrow
                            await self.send_event(ControlEvent(EventType.ROTATE, 1))
                elif ch == ' ':
                    await self.send_event(ControlEvent(EventType.PRESS))
                elif ch == '\r':  # Enter
                    await self.send_event(ControlEvent(EventType.LONG_PRESS))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if self.ws:
                await self.ws.close()


async def main():
    if GPIO_AVAILABLE:
        encoder = RotaryEncoder()
    else:
        encoder = SimulatedEncoder()
    
    await encoder.run()


if __name__ == "__main__":
    asyncio.run(main())
