#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.3.0-beta}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
BUILD="$(mktemp -d)"
APP="$BUILD/spectra-hud-$VERSION"

cleanup() {
    rm -rf "$BUILD"
}
trap cleanup EXIT

mkdir -p "$DIST" "$APP/docs"
cd "$ROOT"

cp ai_client.py config.py demo.py fonts.py i18n.py ipc.py main.py overlay.py \
    prompt_system.md requirements.txt requirements-dev.txt results.py \
    screen_capture.py session_memory.py settings.py theme.py tray.py \
    wayland_capture.py widgets.py \
    install.sh run.sh README.md LICENSE NOTICE .env.example pyproject.toml \
    "$APP/"
cp docs/CONFIG.md docs/I18N.md docs/LGPD.md docs/PROVIDERS.md \
    docs/THEMES.md docs/TROUBLESHOOTING.md docs/WAYLAND.md "$APP/docs/"
chmod 755 "$APP/install.sh" "$APP/run.sh"

tar -czf "$DIST/spectra-hud-${VERSION}.tar.gz" -C "$BUILD" "spectra-hud-$VERSION"
echo "Built $DIST/spectra-hud-${VERSION}.tar.gz"
