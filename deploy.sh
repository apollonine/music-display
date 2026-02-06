#!/bin/bash
# One-command deployment for Raspberry Pi

set -e

echo "🎵 Music Display Raspberry Pi Deployment"
echo "========================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is optimized for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
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
    i2c-tools \
    spi-tools \
    nginx \
    supervisor

# Enable I2C and SPI
echo "🔌 Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Clone or update repository
REPO_DIR="/home/pi/music-display"
if [ -d "$REPO_DIR" ]; then
    echo "📥 Updating existing repository..."
    cd "$REPO_DIR"
    git pull
else
    echo "📥 Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/music-display.git "$REPO_DIR"
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

# Install hardware-specific packages
echo "🖥️  Installing hardware packages..."
pip install RPi.GPIO waveshare-epd luma.oled

# Create environment file
echo "⚙️  Setting up configuration..."
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
User=pi
WorkingDirectory=$REPO_DIR/backend
Environment=PATH=$REPO_DIR/backend/venv/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=$REPO_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create hybrid display service
echo "🖥️  Creating hybrid display service..."
sudo tee /etc/systemd/system/hybrid-display.service > /dev/null <<EOF
[Unit]
Description=Music Display Hybrid Controller
After=network.target music-display.service

[Service]
Type=simple
User=pi
WorkingDirectory=$REPO_DIR/hardware
Environment=PATH=$REPO_DIR/backend/venv/bin
ExecStart=$REPO_DIR/backend/venv/bin/python3 hybrid_controller.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Setup nginx
echo "🌐 Setting up nginx..."
sudo tee /etc/nginx/sites-available/music-display > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
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
sudo systemctl enable hybrid-display
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
echo "🎉 Deployment complete!"
echo "======================="
echo "📍 Web interface: http://$(hostname -I | awk '{print $1}')"
echo "📝 Edit configuration: nano $REPO_DIR/backend/.env"
echo "📊 Check backend logs: sudo journalctl -u music-display -f"
echo "🖥️  Check display logs: sudo journalctl -u hybrid-display -f"
echo ""
echo "🔑 Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Restart: sudo systemctl restart music-display"
echo "3. Connect hardware (e-ink, OLED, microphone)"
echo "4. Enable display: sudo systemctl start hybrid-display"
