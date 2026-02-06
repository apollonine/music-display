from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import asyncio
from typing import Optional
import json

from .config import get_settings
from .models import DisplayState, DisplayMode, TrackInfo, ControlEvent
from .services.spotify_service import spotify_service
from .services.fingerprint_service import fingerprint_service
from .services.lyrics_service import lyrics_service
from .services.demo_service import demo_service
from .services.lastfm_service import lastfm_service
from .services.audio_listener import audio_listener


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()
display_state = DisplayState()
current_track: Optional[TrackInfo] = None
polling_task: Optional[asyncio.Task] = None


def get_active_source() -> str:
    """Determine which music source to use based on configuration."""
    settings = get_settings()
    
    if settings.spotify_client_id and settings.spotify_client_secret:
        return "spotify"
    elif settings.lastfm_api_key and settings.lastfm_username:
        return "lastfm"
    elif settings.enable_audio_listener and settings.acoustid_api_key:
        return "audio"
    else:
        return "demo"


def is_demo_mode() -> bool:
    """Check if we should use demo mode."""
    return get_active_source() == "demo"


async def poll_music_source():
    """Background task to poll for current track from configured source."""
    global current_track, display_state
    
    source = get_active_source()
    print(f"Music source: {source.upper()}")
    
    poll_count = 0
    while True:
        try:
            track = None
            poll_count += 1
            
            if source == "demo":
                track = demo_service.get_current_track()
            elif source == "lastfm":
                track = await lastfm_service.get_current_track()
                if poll_count % 10 == 0:  # Log every 5 seconds
                    print(f"[Last.fm] Polling... Track: {track.title if track else 'None'}")
            elif source == "spotify" and spotify_service.is_authenticated():
                track = await spotify_service.get_current_track()
            
            if track:
                if not current_track or track.id != current_track.id:
                    # New track - fetch lyrics
                    if not track.lyrics:
                        lyrics = await lyrics_service.get_lyrics(track.artist, track.title)
                        track.lyrics = lyrics
                    
                    current_track = track
                    display_state.track = track
                    
                    await manager.broadcast({
                        "type": "track_update",
                        "track": track.model_dump()
                    })
                else:
                    # Update progress
                    if source == "demo":
                        track = demo_service.get_current_track()
                    current_track.progress_ms = track.progress_ms if track else current_track.progress_ms
                    current_track.is_playing = track.is_playing if track else current_track.is_playing
                    
                    await manager.broadcast({
                        "type": "progress_update",
                        "progress_ms": current_track.progress_ms,
                        "is_playing": current_track.is_playing
                    })
                    
        except Exception as e:
            print(f"Polling error: {e}")
        
        await asyncio.sleep(0.5)


async def on_audio_track_identified(track: TrackInfo):
    """Callback when audio listener identifies a track."""
    global current_track, display_state
    
    if not current_track or track.id != current_track.id:
        lyrics = await lyrics_service.get_lyrics(track.artist, track.title)
        track.lyrics = lyrics
        current_track = track
        display_state.track = track
        
        await manager.broadcast({
            "type": "track_update",
            "track": track.model_dump()
        })


@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task
    settings = get_settings()
    
    polling_task = asyncio.create_task(poll_music_source())
    
    # Start audio listener if enabled
    audio_listener_task = None
    if settings.enable_audio_listener and audio_listener.is_available():
        audio_listener.set_callback(on_audio_track_identified)
        audio_listener_task = asyncio.create_task(audio_listener.start_listening())
        print("Audio listener started")
    
    yield
    
    if polling_task:
        polling_task.cancel()
    if audio_listener_task:
        audio_listener.stop_listening()
        audio_listener_task.cancel()


app = FastAPI(
    title="Music Display API",
    description="Backend for intelligent tabletop music display",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "Music Display API",
        "version": "0.1.0",
        "spotify_authenticated": spotify_service.is_authenticated()
    }


@app.get("/auth/spotify")
async def spotify_auth():
    """Initiate Spotify OAuth flow."""
    auth_url = spotify_service.get_auth_url()
    if not auth_url:
        raise HTTPException(status_code=500, detail="Spotify not configured")
    return RedirectResponse(auth_url)


@app.get("/callback")
async def spotify_callback(code: str = Query(...)):
    """Handle Spotify OAuth callback."""
    success = spotify_service.handle_callback(code)
    if success:
        return RedirectResponse("http://localhost:5173?auth=success")
    raise HTTPException(status_code=400, detail="Authentication failed")


@app.get("/auth/status")
async def auth_status():
    """Check authentication status and available sources."""
    settings = get_settings()
    return {
        "spotify": spotify_service.is_authenticated(),
        "lastfm": lastfm_service.is_configured(),
        "audio_listener": settings.enable_audio_listener and audio_listener.is_available(),
        "demo_mode": is_demo_mode(),
        "active_source": get_active_source()
    }


@app.get("/track/current")
async def get_current_track():
    """Get currently playing track."""
    if current_track:
        return current_track.model_dump()
    return None


@app.get("/display/state")
async def get_display_state():
    """Get current display state."""
    return display_state.model_dump()


@app.post("/display/mode/{mode}")
async def set_display_mode(mode: DisplayMode):
    """Change display mode."""
    global display_state
    display_state.mode = mode
    await manager.broadcast({
        "type": "mode_change",
        "mode": mode.value
    })
    return {"mode": mode.value}


@app.post("/control/play-pause")
async def control_play_pause():
    """Toggle play/pause."""
    if is_demo_mode():
        demo_service.toggle_play_pause()
        return {"success": True}
    success = await spotify_service.play_pause()
    return {"success": success}


@app.post("/control/next")
async def control_next():
    """Skip to next track."""
    global current_track
    if is_demo_mode():
        demo_service.next_track()
        current_track = None
        return {"success": True}
    success = await spotify_service.next_track()
    return {"success": success}


@app.post("/control/previous")
async def control_previous():
    """Go to previous track."""
    global current_track
    if is_demo_mode():
        demo_service.previous_track()
        current_track = None
        return {"success": True}
    success = await spotify_service.previous_track()
    return {"success": success}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await manager.connect(websocket)
    
    # Send current state on connect
    await websocket.send_json({
        "type": "init",
        "state": display_state.model_dump(),
        "track": current_track.model_dump() if current_track else None
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            # Handle control events from hardware/touch
            if event.get("type") == "control":
                control = ControlEvent(**event.get("data", {}))
                await handle_control_event(control)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
        await spotify_service.play_pause()
    
    elif event.type == "long_press":
        # Long press - next track
        await spotify_service.next_track()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
