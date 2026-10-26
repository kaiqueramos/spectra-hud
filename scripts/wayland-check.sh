#!/usr/bin/env bash
# Wayland smoke test: run inside a real Wayland session, from the repo root.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

echo "== Session"
echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unset}"
echo "XDG_CURRENT_DESKTOP=${XDG_CURRENT_DESKTOP:-unset}"
echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset}"
echo "DISPLAY=${DISPLAY:-unset}"

if [ "${XDG_SESSION_TYPE:-}" != "wayland" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo
    echo "Not a Wayland session. Log in to \"Ubuntu on Wayland\" and run this again."
    exit 2
fi

echo
echo "== Capture backends"
for tool in grim gnome-screenshot spectacle; do
    printf '%-20s %s\n' "$tool" "$(command -v "$tool" || echo 'not installed')"
done

echo
echo "== Portal"
if command -v gdbus >/dev/null 2>&1 &&
    gdbus introspect --session --dest org.freedesktop.portal.Desktop \
        --object-path /org/freedesktop/portal/desktop 2>/dev/null |
        grep -q 'org.freedesktop.portal.Screenshot'; then
    echo "Screenshot portal: available"
else
    echo "Screenshot portal: NOT available"
fi

echo
echo "== Tray dependencies"
python3 - <<'EOF'
try:
    import gi
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3  # noqa: F401
    print("gi + AyatanaAppIndicator3: ok")
except Exception as exc:
    print(f"gi + AyatanaAppIndicator3: missing ({exc})")
EOF

echo
echo "== Capture test (may show a portal permission dialog)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY=python3
OUT="${XDG_RUNTIME_DIR:-/tmp}/spectra-wayland-test.png"
PYTHONPATH="$ROOT" "$PY" - "$OUT" <<'EOF'
import sys
import time

from PIL import Image

import wayland_capture

out = sys.argv[1]
start = time.time()
try:
    img, monitor = wayland_capture.capture_wayland()
    img.save(out)
    print(f"capture: ok {img.width}x{img.height} in {time.time() - start:.1f}s")
    print(f"monitor: {monitor}")
    print(f"saved:   {out}")
except Exception as exc:
    print(f"capture: FAILED after {time.time() - start:.1f}s")
    print(f"reason:  {exc}")
    sys.exit(1)
EOF

status=$?
echo
if [ "$status" -ne 0 ]; then
    echo "Result: FAILED. Install a fallback and try again:"
    echo "  GNOME: sudo apt install gnome-screenshot"
    echo "  KDE:   sudo apt install spectacle"
    echo "  Sway:  sudo apt install grim"
    exit "$status"
fi
echo "Result: capture works. Next: run ./run.sh and bind a system shortcut to:"
echo "  $ROOT/run.sh --scan"
