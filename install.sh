#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "==> Checking system dependencies"
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
python3 - <<'EOF' || { echo "Tkinter missing: sudo apt install python3-tk"; exit 1; }
import tkinter  # noqa: F401
EOF
if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
  echo "Wayland session detected: running the beta (portal capture, Results panel)."
  command -v grim >/dev/null || command -v gnome-screenshot >/dev/null || command -v spectacle >/dev/null || \
    echo "WARN: install a capture fallback: gnome-screenshot, spectacle or grim."
else
  if ! command -v xdotool >/dev/null; then
    echo "WARN: xdotool not found (sudo apt install xdotool)."
    echo "      Multi-monitor capture will fall back to the primary monitor."
  fi
fi
if ! python3 -c "import gi" >/dev/null 2>&1; then
  echo "WARN: python3-gi not found; the tray needs it (sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1)."
fi

echo "==> Checking python3-venv"
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  echo "ERROR: python3-venv (ensurepip) is required."
  echo "  Ubuntu/Debian: sudo apt install python3-venv"
  echo "  Fedora/Arch:   install the distro package that provides python3 venv/ensurepip"
  exit 1
fi

echo "==> Creating virtualenv"
python3 -m venv --system-site-packages .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo "==> Created optional .env for CI/headless; the command center stores the key in the keyring"
else
  echo "==> .env already exists, leaving it untouched"
fi

chmod +x run.sh

echo "==> Registering desktop entry"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/spectra-hud.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Spectra HUD
Comment=Screen-aware AI HUD
Exec=$ROOT/run.sh
Path=$ROOT
Icon=utilities-terminal
Terminal=true
Categories=Utility;
Actions=Scan;Ask;Open;

[Desktop Action Scan]
Name=Scan screen
Exec=$ROOT/run.sh --scan

[Desktop Action Ask]
Name=Ask about the screen
Exec=$ROOT/run.sh --ask

[Desktop Action Open]
Name=Command center
Exec=$ROOT/run.sh --show
EOF

echo
echo "Done. Next:"
echo "  1) run: $ROOT/run.sh"
echo "  2) the first run opens the command center: choose provider, paste key, test vision, consent and save"
