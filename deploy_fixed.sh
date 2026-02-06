#!/bin/bash
# Fixed deployment with proper nginx configuration

set -e

echo "🎵 Music Display Fixed Deployment"
echo "================================="

# Get current user dynamically
CURRENT_USER=$(whoami)
HOME_DIR="/home/$CURRENT_USER"

echo "👤 Detected user: $CURRENT_USER"
echo "🏠 Home directory: $HOME_DIR"

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

# Build frontend
echo "🎨 Building frontend..."
cd "$REPO_DIR/frontend"
npm install
npm run build

# Fix nginx configuration
echo "🌐 Fixing nginx configuration..."
sudo tee /etc/nginx/sites-available/music-display > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    root $REPO_DIR/frontend/dist;
    index index.html;
    
    # Handle frontend routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Test and restart nginx
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Nginx configuration fixed!"
echo ""
echo "🌐 Test the site:"
echo "curl http://localhost/"
echo ""
echo "🖥️  Open in browser:"
echo "chromium http://localhost"
