"""
Main FastAPI application for Music Display
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import get_settings
from .models import (
    TrackInfo, DisplayMode, DisplayState, ControlEvent,
    SourceType
)
from .services import (
    spotify_service, lastfm_service, audio_listener,
    demo_service, lyrics_service
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)


manager = ConnectionManager()
display_state = DisplayState()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.enable_audio_listener:
        asyncio.create_task(audio_listener.start())
    
    yield
    
    # Cleanup
    if settings.enable_audio_listener:
        audio_listener.stop()


app = FastAPI(
    title="Music Display API",
    version="0.1.0",
    lifespan=lifespan
)


# API Routes
@app.get("/auth/status")
async def get_auth_status():
    """Get authentication status for all services."""
    return {
        "name": "Music Display API",
        "version": "0.1.0",
        "spotify_authenticated": spotify_service.is_authenticated(),
        "lastfm_available": lastfm_service.is_available(),
        "audio_listener_available": audio_listener.is_available(),
        "demo_mode": not any([
            spotify_service.is_authenticated(),
            lastfm_service.is_available(),
            audio_listener.is_available()
        ]),
        "active_source": display_state.active_source
    }


@app.get("/track/current")
async def get_current_track() -> Optional[TrackInfo]:
    """Get currently playing track."""
    return display_state.track


@app.post("/control/play-pause")
async def play_pause():
    """Toggle play/pause."""
    if spotify_service.is_authenticated():
        await spotify_service.play_pause()
    return {"status": "ok"}


@app.post("/control/next")
async def next_track():
    """Skip to next track."""
    if spotify_service.is_authenticated():
        await spotify_service.next_track()
    return {"status": "ok"}


@app.post("/control/previous")
async def previous_track():
    """Go to previous track."""
    if spotify_service.is_authenticated():
        await spotify_service.previous_track()
    return {"status": "ok"}


@app.post("/control/mode")
async def set_mode(mode: DisplayMode):
    """Set display mode."""
    display_state.mode = mode
    await manager.broadcast({
        "type": "mode_change",
        "mode": mode.value
    })
    return {"status": "ok", "mode": mode.value}


@app.post("/control/event")
async def handle_control_event(event: ControlEvent):
    """Handle physical/touch control events."""
    global display_state

    if event.type == "rotate":
        # Rotary encoder rotation - cycle display modes
        modes = list(DisplayMode)
        current_idx = modes.index(display_state.mode)
        new_idx = (current_idx + (event.value or 1)) % len(modes)
        display_state.mode = modes[new_idx]

        await manager.broadcast({
            "type": "mode_change",
            "mode": display_state.mode.value
        })

    elif event.type == "press":
        # Button press - play/pause
        if spotify_service.is_authenticated():
            await spotify_service.play_pause()

    elif event.type == "long_press":
        # Long press - next track
        if spotify_service.is_authenticated():
            await spotify_service.next_track()

    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send current state on connect
        await websocket.send_text({
            "type": "track_update",
            "track": display_state.track.dict() if display_state.track else None
        })
        await websocket.send_text({
            "type": "mode_change",
            "mode": display_state.mode.value
        })
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Mount static files
app.mount("/static", StaticFiles(directory="../frontend/dist/assets"), name="static")

# Serve the React app - THIS MUST BE LAST
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve the React application."""
    return FileResponse("../frontend/dist/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
