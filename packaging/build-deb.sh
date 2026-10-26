#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.2.1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
BUILD="$(mktemp -d)"
PKG="$BUILD/pkg"
APP="$PKG/opt/spectra-hud"

cleanup() {
    rm -rf "$BUILD"
}
trap cleanup EXIT

mkdir -p "$DIST" "$APP" "$PKG/DEBIAN" "$PKG/usr/bin" \
    "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/scalable/apps" \
    "$PKG/usr/share/doc/spectra-hud"

cd "$ROOT"
APP_FILES=(
    ai_client.py config.py demo.py fonts.py i18n.py ipc.py main.py overlay.py
    prompt_system.md requirements.txt results.py screen_capture.py
    session_memory.py settings.py theme.py tray.py wayland_capture.py widgets.py
)
cp "${APP_FILES[@]}" "$APP/"
cp LICENSE NOTICE README.md "$PKG/usr/share/doc/spectra-hud/"
install -m 755 packaging/spectra-hud.launcher "$PKG/usr/bin/spectra-hud"
install -m 644 packaging/spectra-hud.desktop "$PKG/usr/share/applications/spectra-hud.desktop"
install -m 644 docs/favicon.svg "$PKG/usr/share/icons/hicolor/scalable/apps/spectra-hud.svg"

cat > "$PKG/DEBIAN/control" <<EOF
Package: spectra-hud
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: Kaique Rodrigues Ramos <57043366+kaiqueramos@users.noreply.github.com>
Depends: python3 (>= 3.10), python3-venv, python3-tk, python3-gi, gir1.2-ayatanaappindicator3-0.1, libx11-6
Recommends: xdotool, gnome-keyring, gir1.2-ayatanaappindicator3-0.1
Homepage: https://github.com/kaiqueramos/spectra-hud
Description: Screen-aware AI HUD for Linux/X11
 Press a hotkey and Spectra reads the active screen, then anchors up to
 three actionable cards to the elements that matter. Bring your own
 OpenAI-compatible vision provider or use a local Ollama model.
EOF

cat > "$PKG/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
APP=/opt/spectra-hud
if [ ! -x "$APP/.venv/bin/python" ] || ! "$APP/.venv/bin/python" -c "import gi" >/dev/null 2>&1; then
    echo "Spectra HUD: creating Python environment (needs internet)..."
    python3 -m venv --clear --system-site-packages "$APP/.venv"
fi
"$APP/.venv/bin/python" -m pip install --no-cache-dir --disable-pip-version-check \
    -r "$APP/requirements.txt"
echo "Spectra HUD installed. Run: spectra-hud"
EOF

cat > "$PKG/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    rm -rf /opt/spectra-hud/.venv
    rmdir /opt/spectra-hud 2>/dev/null || true
fi
EOF

chmod 755 "$PKG/DEBIAN/postinst" "$PKG/DEBIAN/postrm"
dpkg-deb --build --root-owner-group "$PKG" \
    "$DIST/spectra-hud_${VERSION}_all.deb"
echo "Built $DIST/spectra-hud_${VERSION}_all.deb"
