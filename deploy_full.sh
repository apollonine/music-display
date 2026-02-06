#!/bin/bash
# Full deployment with frontend for DSI display

set -e

echo "🎵 Music Display Full Deployment (DSI + Frontend)"
echo "=================================================="

# Get current user dynamically
CURRENT_USER=$(whoami)
HOME_DIR="/home/$CURRENT_USER"

echo "👤 Detected user: $CURRENT_USER"
echo "🏠 Home directory: $HOME_DIR"

# Check if we're in a home directory
if [ ! -d "$HOME_DIR" ]; then
    echo "❌ Home directory not found: $HOME_DIR"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    portaudio19-dev \
    libasound2-dev \
    libportaudiocpp0 \
    nginx \
    supervisor \
    curl \
    gnupg

# Install Node.js for frontend
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Enable I2C
echo "🔌 Enabling I2C..."
sudo raspi-config nonint do_i2c 0

# Clone or update repository
REPO_DIR="$HOME_DIR/music-display"
if [ -d "$REPO_DIR" ]; then
    echo "📥 Updating existing repository..."
    cd "$REPO_DIR"
    git pull
else
    echo "📥 Cloning repository..."
    git clone https://github.com/apollonine/music-display.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd "$REPO_DIR/backend"
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install only what we need for DSI display
echo "🖥️  Installing display packages..."
pip install RPi.GPIO

# Build frontend
echo "🎨 Building frontend..."
cd "$REPO_DIR/frontend"
npm install
npm run build

# Create environment file
echo "⚙️  Setting up configuration..."
cd "$REPO_DIR/backend"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file - please edit with your API keys:"
    echo "   nano $REPO_DIR/backend/.env"
fi

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/music-display.service > /dev/null <<EOF
[Unit]
Description=Music Display Backend
After=network.target sound.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$REPO_DIR/backend
Environment=PATH=$REPO_DIR/backend/venv/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=$REPO_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Setup nginx to serve frontend
echo "🌐 Setting up nginx..."
sudo tee /etc/nginx/sites-available/music-display > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    root $REPO_DIR/frontend/dist;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/music-display /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable music-display
sudo systemctl start music-display

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "❌ Backend failed to start. Check logs with:"
    echo "   sudo journalctl -u music-display -f"
fi

echo ""
echo "🎉 Full deployment complete!"
echo "============================"
echo "📍 Web interface: http://$(hostname -I | awk '{print $1}')"
echo "📝 Edit configuration: nano $REPO_DIR/backend/.env"
echo "📊 Check backend logs: sudo journalctl -u music-display -f"
echo ""
echo "🔑 Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Restart: sudo systemctl restart music-display"
echo "3. Open browser on the Pi: chromium http://localhost"
echo "4. Or access from other device: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "🖥️  DSI Display Notes:"
echo "- Frontend is built and served by nginx"
echo "- WebSocket connects to backend for real-time updates"
echo "- Open chromium --kiosk http://localhost for fullscreen display"
