#!/bin/bash
# --- Configuration ---
SERVICE_NAME="phonotify"
PYTHON_BIN=$(which python3)
PROJECT_DIR=$(pwd)
CODE_DIR="src"
MAIN_SCRIPT="main.py"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
PYTHON_DEPENDENCIES="requirements.txt"

echo "Installing System Dependencies (needs sudo)..."
# Arch equivalents: python-gobject for gi, libappindicator-gtk3 for tray support
sudo pacman -S --needed --noconfirm python tk python-gobject libappindicator-gtk3

# Helper: check if an existing venv has --system-site-packages enabled
venv_has_system_site_packages() {
    local venv_cfg="$1/pyvenv.cfg"
    if [[ -f "$venv_cfg" ]]; then
        grep -qi "include-system-site-packages\s*=\s*true" "$venv_cfg"
        return $?
    fi
    return 1
}

# 1. Detect Python path (Check for venv)
if [[ -n "$VIRTUAL_ENV" ]]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python3"
    echo "Active venv detected: Using $PYTHON_BIN"
    if ! venv_has_system_site_packages "$VIRTUAL_ENV"; then
        echo "WARNING: Active venv lacks --system-site-packages (gi/gobject won't be accessible)."
        echo "Recreating venv with --system-site-packages..."
        $PYTHON_BIN -m venv --system-site-packages "$VIRTUAL_ENV"
        echo "Venv recreated at $VIRTUAL_ENV"
    fi
elif [[ -f "venv/bin/python3" ]]; then
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
    echo "Found venv folder: Using $PYTHON_BIN"
    if ! venv_has_system_site_packages "$PROJECT_DIR/venv"; then
        echo "WARNING: Existing venv lacks --system-site-packages (gi/gobject won't be accessible)."
        echo "Recreating venv with --system-site-packages..."
        rm -rf "$PROJECT_DIR/venv"
        $(which python3) -m venv --system-site-packages "$PROJECT_DIR/venv"
        echo "Venv recreated at $PROJECT_DIR/venv"
    fi
else
    echo "No venv detected"
    echo "Creating new venv with --system-site-packages..."
    # --system-site-packages is required on Arch so gi/gobject (pacman-managed) is accessible in venv
    $PYTHON_BIN -m venv --system-site-packages venv
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
    echo "Using $PYTHON_BIN"
fi

echo "Installing Python dependencies..."
if [[ -f "$PYTHON_DEPENDENCIES" ]]; then
    $PYTHON_BIN -m pip install -r "$PYTHON_DEPENDENCIES"
else
    echo "ERROR: No $PYTHON_DEPENDENCIES file found"
    exit 1
fi

# Quick sanity check for gi
if ! $PYTHON_BIN -c "import gi" 2>/dev/null; then
    echo "ERROR: 'gi' module still not importable after venv setup."
    echo "Make sure python-gobject is installed: sudo pacman -S python-gobject"
    exit 1
fi
echo "gi module OK"

echo "Starting installation for $SERVICE_NAME..."

# 2. Create systemd user directory if it doesn't exist
mkdir -p "$SYSTEMD_USER_DIR"

# 3. Grant Bluetooth capabilities to Python
echo "Granting BLE permissions to Python..."
# On Arch, libcap provides setcap — install it if missing
sudo pacman -S --needed --noconfirm libcap
sudo setcap 'cap_net_raw,cap_net_admin+eip' "$(readlink -f "$PYTHON_BIN")"

# 4. Create the systemd service file
echo "Creating service file..."
cat <<EOF > "$SYSTEMD_USER_DIR/$SERVICE_NAME.service"
[Unit]
Description=Phonotify Tray Application
After=network.target graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_BIN $PROJECT_DIR/$CODE_DIR/$MAIN_SCRIPT
Environment=PYTHONUNBUFFERED=1
# Wayland/Hyprland: WAYLAND_DISPLAY is the key one; DISPLAY for XWayland fallback
PassEnvironment=DISPLAY XAUTHORITY WAYLAND_DISPLAY XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical-session.target
EOF

# 5. Refresh and start
echo "Reloading systemd and starting service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"
systemctl --user restart "$SERVICE_NAME.service" &

echo "-------------------------------------------------------"
echo "Installation      Complete!"
echo "Service Status:   systemctl --user status $SERVICE_NAME.service"
echo "View Logs:        journalctl --user -u $SERVICE_NAME -f"
echo "-------------------------------------------------------"
