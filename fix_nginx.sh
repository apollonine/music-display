#!/bin/bash
# Quick nginx fix

echo "🔧 Fixing nginx configuration..."

# Get current user
CURRENT_USER=$(whoami)
REPO_DIR="/home/$CURRENT_USER/music-display"

# Create simple working nginx config
sudo tee /etc/nginx/sites-available/music-display > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    root /home/pi/music-display/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
EOF

# Test and restart
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Nginx fixed!"
echo "Test: curl http://localhost/"
