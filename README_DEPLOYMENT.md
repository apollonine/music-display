# Raspberry Pi Deployment Guide

## Option 1: One-Command Deploy (Easiest)

Run this single command on your Raspberry Pi:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/music-display/main/deploy.sh | bash
```

That's it! The script will:
- ✅ Update system packages
- ✅ Install all dependencies
- ✅ Clone the repository
- ✅ Setup Python environment
- ✅ Configure nginx
- ✅ Create systemd services
- ✅ Start everything automatically

## Option 2: Manual Deploy

If you prefer to run steps manually:

```bash
# 1. SSH into Raspberry Pi
ssh pi@raspberrypi.local

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/music-display.git
cd music-display

# 3. Run deployment script
./deploy.sh
```

## After Deployment

### 1. Configure API Keys

```bash
nano /home/pi/music-display/backend/.env
```

Add your keys:
```bash
# Get these from the services
LASTFM_API_KEY=your_key_here
ACOUSTID_API_KEY=your_key_here
ENABLE_AUDIO_LISTENER=true
```

### 2. Restart Services

```bash
sudo systemctl restart music-display
```

### 3. Access the Interface

Open browser to: `http://raspberrypi.local`

## Hardware Setup (Optional)

### E-ink + OLED Display

```bash
# Enable display service
sudo systemctl start hybrid-display

# Check status
sudo systemctl status hybrid-display
```

### Microphone Setup

```bash
# Test microphone
arecord -D plughw:1,0 -d 5 test.wav
aplay test.wav

# If no sound, edit:
sudo nano /usr/share/alsa/alsa.conf
# Add: defaults.pcm.card 1
```

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
sudo journalctl -u music-display -f

# Common fix: Install missing packages
sudo apt install portaudio19-dev libasound2-dev
```

### Display Not Working
```bash
# Check I2C/SPI
sudo i2cdetect -y 1
ls /dev/spi*

# Check display logs
sudo journalctl -u hybrid-display -f
```

### Microphone Issues
```bash
# List audio devices
arecord -l

# Test audio recording
arecord -D plughw:1,0 -d 3 test.wav
```

## Services Management

```bash
# Start/Stop services
sudo systemctl start music-display
sudo systemctl stop music-display
sudo systemctl restart music-display

# Enable on boot
sudo systemctl enable music-display
sudo systemctl enable hybrid-display

# Check status
sudo systemctl status music-display
sudo systemctl status hybrid-display
```

## Performance Tips

1. **Use Raspberry Pi 4** for best performance
2. **Add heatsinks** for continuous operation
3. **Use high-quality SD card** (32GB+ Class 10)
4. **Disable GUI** if not needed: `sudo raspi-config nonint do_boot_cli`

## Updates

To update to latest version:

```bash
cd /home/pi/music-display
git pull
sudo systemctl restart music-display
sudo systemctl restart hybrid-display
```
