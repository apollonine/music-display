# Music Display

An intelligent tabletop music display system that automatically identifies what's playing (from Spotify or analog sources like vinyl), fetches rich metadata, and displays dynamic visualizations on a premium touchscreen.

## Features

- **Automatic Music Recognition**
  - Spotify integration with real-time track detection (<500ms)
  - Audio fingerprinting for analog sources (vinyl, tape, CD) via AcoustID/Chromaprint
  
- **Rich Visual Experience**
  - 5 display modes: Album Art, Lyrics, Artist Info, Visualizer, Minimal
  - Dynamic color extraction from album artwork
  - Smooth 60fps animations with Framer Motion
  
- **Physical Controls**
  - Rotary encoder support (rotate to change modes, press to play/pause)
  - Touch-enabled interface
  - Keyboard controls for development

## Project Structure

```
music-display/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py           # API endpoints & WebSocket
│   │   ├── config.py         # Configuration
│   │   ├── models.py         # Pydantic models
│   │   └── services/
│   │       ├── spotify_service.py      # Spotify API integration
│   │       ├── fingerprint_service.py  # Audio fingerprinting
│   │       └── lyrics_service.py       # Lyrics fetching
│   └── requirements.txt
├── frontend/          # React + TypeScript frontend
│   └── src/
│       ├── components/       # Display mode components
│       ├── hooks/            # WebSocket & color extraction
│       └── types.ts          # TypeScript definitions
├── hardware/          # Raspberry Pi GPIO interface
│   ├── rotary_encoder.py     # Rotary encoder controller
│   ├── eink_display.py       # E-ink display driver
│   ├── oled_status.py        # OLED status bar driver
│   └── hybrid_controller.py  # Hybrid display coordinator
└── docs/              # Documentation
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Spotify Developer Account (for API credentials)
- AcoustID API Key (for analog source recognition)
- Chromaprint (`brew install chromaprint` on macOS)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Connect Spotify

1. Open http://localhost:5173 in your browser
2. Click "Connect Spotify"
3. Authorize the application
4. Start playing music on any Spotify device

## Music Sources

The system supports multiple music sources. Configure one in your `.env` file:

### Option 1: Last.fm (Recommended)
Works with any music player that scrobbles to Last.fm (Spotify, Apple Music, Plex, etc.)

1. Go to [Last.fm API](https://www.last.fm/api/account/create)
2. Create an application (instant approval)
3. Add to `.env`:
   ```
   LASTFM_API_KEY=your_api_key
   LASTFM_USERNAME=your_username
   ```

### Option 2: Audio Fingerprinting (Vinyl/Analog)
Listens via microphone and identifies tracks using AcoustID.

1. Register at [AcoustID](https://acoustid.org/new-application)
2. Install chromaprint: `brew install chromaprint`
3. Add to `.env`:
   ```
   ACOUSTID_API_KEY=your_api_key
   ENABLE_AUDIO_LISTENER=true
   ```

### Option 3: Spotify (Currently Unavailable)
Spotify has paused new API integrations. If you have existing credentials:

1. Add `http://localhost:8000/callback` to Redirect URIs
2. Add to `.env`:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

### Demo Mode
If no credentials are configured, the system runs in demo mode with sample tracks.

## Display Modes

| Mode | Description |
|------|-------------|
| **Album Art** | Large album artwork with animated background, progress bar, vinyl effect |
| **Lyrics** | Split view with album art and scrolling lyrics |
| **Artist Info** | Artist photo, genres, and current track info |
| **Visualizer** | Animated audio visualizer bars |
| **Minimal** | Clean, distraction-free display |

## Controls

### Keyboard (Development)
- `←` / `→` - Switch display modes
- `Space` - Play/Pause

### Rotary Encoder (Hardware)
- Rotate - Switch display modes
- Press - Play/Pause
- Long Press - Next track

### Touch
- Tap mode icons at bottom of screen

## Hardware Setup (Raspberry Pi)

### Option 1: Web Display (Touchscreen)
Use the React frontend on a 7" touchscreen.

### Option 2: Hybrid Display (E-ink + OLED)
E-ink for album art, OLED for progress bar. Low power, always-on.

#### Shopping List
| Component | Model | Cost |
|-----------|-------|------|
| E-ink Display | Waveshare 7.5" v2 (800x480) | ~$55 |
| OLED Status | SSD1306 1.3" (128x64) | ~$8 |
| Raspberry Pi | Pi 4 (2GB+) | ~$55 |
| USB Microphone | Any USB mic | ~$15 |

#### Wiring

**E-ink (SPI):**
| E-ink Pin | Pi GPIO |
|-----------|---------|
| VCC | 3.3V |
| GND | GND |
| DIN | GPIO 10 (MOSI) |
| CLK | GPIO 11 (SCLK) |
| CS | GPIO 8 (CE0) |
| DC | GPIO 25 |
| RST | GPIO 17 |
| BUSY | GPIO 24 |

**OLED (I2C):**
| OLED Pin | Pi GPIO |
|----------|---------|
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO 2 |
| SCL | GPIO 3 |

**Rotary Encoder (KY-040):**
| Encoder Pin | Pi GPIO |
|-------------|---------|
| CLK | GPIO 17 |
| DT | GPIO 18 |
| SW | GPIO 27 |
| + | 3.3V |
| GND | GND |

#### Running the Hybrid Display

```bash
cd hardware
pip install -r requirements.txt

# On Raspberry Pi, also install:
pip install RPi.GPIO waveshare-epd luma.oled

# Run the hybrid controller
python hybrid_controller.py
```

The hybrid controller connects to the backend via WebSocket and updates:
- **E-ink**: Only when track changes (slow refresh is fine)
- **OLED**: Every second for progress bar

#### Testing Without Hardware

Both displays run in simulation mode on non-Pi systems:
- E-ink preview saved to `/tmp/eink_preview.png`
- OLED preview saved to `/tmp/oled_preview.png`

## Development

### Running Both Servers

```bash
# Terminal 1 - Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Testing Without Hardware

The hardware controller includes a simulation mode that uses keyboard input:
- Left/Right arrows simulate rotation
- Space simulates button press
- Enter simulates long press

## Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│   Frontend      │◄──────────────────►│    Backend      │
│   (React)       │                    │   (FastAPI)     │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │ Touch/Keyboard                       │ Spotify API
         │                                      │ AcoustID API
         ▼                                      │ Lyrics API
┌─────────────────┐     WebSocket              │
│ Rotary Encoder  │◄───────────────────────────┘
│  (Raspberry Pi) │
└─────────────────┘
```

## Roadmap

### Phase 1: Prototype ✅
- [x] Spotify integration
- [x] Basic display modes
- [x] WebSocket real-time updates
- [x] Rotary encoder support

### Phase 2: Enhanced Features
- [ ] Audio input for analog source detection
- [ ] Synchronized lyrics display
- [ ] Music discovery recommendations
- [ ] Multi-room support

### Phase 3: Production
- [ ] Custom enclosure design
- [ ] Power management
- [ ] OTA updates
- [ ] Mobile app companion

## License

MIT
