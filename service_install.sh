#!/bin/bash

# --- Configuration ---
SERVICE_NAME="phonotify"
PYTHON_BIN=$(which python3)
PROJECT_DIR=$(pwd)
CODE_DIR="src"
MAIN_SCRIPT="main.py" # Ensure this matches your filename
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
PYTHON_DEPENDENCIES="requirements.txt"


echo "Installing System Dependencies (needs sudo)..."
sudo apt install -y python3-tk python3-venv libayatana-appindicator3-1

# 1. Detect Python path (Check for venv)
if [[ -n "$VIRTUAL_ENV" ]]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python3"
    echo "env detected: Using venv Python -> $PYTHON_BIN"
elif [[ -f "venv/bin/python3" ]]; then
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
    echo "Found venv folder: Using $PYTHON_BIN"
else
    echo "No venv detected"
    echo "Creating new venv...."
    $PYTHON_BIN -m venv --system-site-packages venv
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
    echo "Using $PYTHON_BIN"
    #echo "No venv detected: Using system Python -> $PYTHON_BIN"
fi

echo "Installing dependencies... "
if [[ -f "$PYTHON_DEPENDENCIES" ]]; then 
    $PYTHON_BIN -m pip install -r $PYTHON_DEPENDENCIES
else 
    echo "ERROR: No $PYTHON_DEPENDENCIES file found"
    exit 1
fi 

echo "Starting installation for $SERVICE_NAME..."

# 1. Create systemd user directory if it doesn't exist
mkdir -p "$SYSTEMD_USER_DIR"

# 2. Grant Bluetooth capabilities to Python
# This allows scanning/connecting without running the script as root
echo "Granting BLE permissions to Python..."
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f "$PYTHON_BIN")

# 3. Create the Universal Systemd Service File
echo "Creating service file..."
cat <<EOF > "$SYSTEMD_USER_DIR/$SERVICE_NAME.service"
[Unit]
Description=Phonotify Tray Application
After=network.target

[Service]
ExecStartPre=/usr/bin/sleep 60
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_BIN $PROJECT_DIR/$CODE_DIR/$MAIN_SCRIPT

# Environment Handling
Environment=PYTHONUNBUFFERED=1
# This allows the service to 'see' your screen on X11 or Wayland
PassEnvironment=DISPLAY XAUTHORITY WAYLAND_DISPLAY

Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 4. Refresh and Start
echo "Reloading systemd and starting service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"
systemctl --user restart "$SERVICE_NAME.service" &

echo "-------------------------------------------------------"
echo "Installation      Complete!"
echo "Service Status:   systemctl --user status $SERVICE_NAME.service"
echo "View Logs:        journalctl --user -u $SERVICE_NAME -f"
echo "-------------------------------------------------------"