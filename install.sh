#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "==> Checking system dependencies"
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
python3 - <<'EOF' || { echo "Tkinter missing: sudo apt install python3-tk"; exit 1; }
import tkinter  # noqa: F401
EOF
if ! command -v xdotool >/dev/null; then
  echo "WARN: xdotool not found (sudo apt install xdotool)."
  echo "      Multi-monitor capture will fall back to the primary monitor."
fi
if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
  echo "WARN: Wayland session detected. Spectra v0.2 supports X11 only."
fi

echo "==> Creating virtualenv"
python3 -m venv .venv
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
EOF

echo
echo "Done. Next:"
echo "  1) run: $ROOT/run.sh"
echo "  2) the first run opens the command center: choose provider, paste key, test vision, consent and save"
