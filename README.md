# Spectra HUD

> A screen-aware HUD for Linux. Press a hotkey, and Spectra looks at your screen and pins 1–3 actionable cards to the exact elements that matter.

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform: Linux X11](https://img.shields.io/badge/platform-Linux%20%7C%20X11-lightgrey.svg)](#requirements)

**Status: v0.1 — experimental.** Linux + X11 only. Bring your own API key. The prompt is Brazilian Portuguese.

[**Website**](https://kaiqueramos.github.io/spectra-hud/) · [**GitHub**](https://github.com/kaiqueramos/spectra-hud) · [**Privacy**](PRIVACY.md)

<p align="center">
  <a href="https://kaiqueramos.github.io/spectra-hud/">
    <img src="docs/og.png" alt="Spectra HUD: your screen, annotated." width="100%">
  </a>
</p>

---

## Why

Most AI assistants wait for you to type. Spectra reads the screen and answers **in place**: a tactical overlay for games, IDEs, dashboards and anything where context is visual.

Press `Ctrl+Alt+Space` → Spectra captures the active monitor, asks a vision model what matters, and draws small cards anchored to the relevant UI elements. Click a card to ask a follow-up; drag it anywhere.

## How it works

1. A global hotkey captures the monitor under the mouse cursor (`mss`).
2. The frame is downscaled to 1600 px and sent as JPEG to an OpenAI-compatible vision endpoint.
3. The model returns up to three insights with an optional `box_2d` (normalized 0–1000).
4. Cards and thin highlights are drawn with Tkinter/X11 next to each element.
5. A 1-hour sliding session memory feeds context into the next scan.

No server, no telemetry. The screenshot goes only to the endpoint **you** configure.

## Features

- Global scan hotkey with toggle and a “scanning” indicator.
- Up to 3 anchored cards, draggable, click-to-ask.
- Global command bar (`Ctrl+Shift+Space`) for free-form questions about the screen.
- Session memory with sliding TTL (1 h).
- Multi-monitor aware (X11).
- Bring your own key: any OpenAI-compatible vision model.
- 41 unit tests.

## Requirements

- Linux with **X11** (Wayland is not supported in v0.1).
- Python **3.10+** with Tkinter (`sudo apt install python3-tk`).
- `xdotool` (`sudo apt install xdotool`).
- An API key for an OpenAI-compatible vision endpoint.

## Quick start

```bash
git clone https://github.com/kaiqueramos/spectra-hud.git
cd spectra-hud
./install.sh
```

The installer creates `.venv`, installs dependencies, copies `.env.example` to `.env` and registers a desktop entry. Edit `.env` with your key, then run:

```bash
./run.sh
```

Manual install:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env
python3 main.py
```

## Configuration

`.env` in the project root (never commit it):

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `SPECTRA_API_KEY` | yes | — | Provider key |
| `SPECTRA_BASE_URL` | no | `https://opencode.ai/zen/go/v1` | OpenAI-compatible base URL |
| `SPECTRA_MODEL` | no | `deepseek-v4.1-flash` | Vision model (provider-specific ID) |
| `SPECTRA_HOTKEY` | no | `<ctrl>+<alt>+<space>` | Scan hotkey (pynput syntax) |
| `SPECTRA_HOTKEY_BAR` | no | `<ctrl>+<shift>+<space>` | Command bar hotkey |

Environment variables override `.env`. Legacy names (`OPENCODE_GO_API_KEY`, `OPENCODE_GO_BASE_URL`, `MODEL_NAME`) still work.

**Hotkey note:** the default is `Ctrl+Alt+Space` because `Ctrl+Space` is the autocomplete shortcut in VS Code and JetBrains IDEs. You can change it with `SPECTRA_HOTKEY`.

## Hotkeys

| Key | Action |
|---|---|
| `Ctrl+Alt+Space` | Scan screen / close HUD |
| `Ctrl+Shift+Space` | Global command bar |
| `Alt+1..3` | Open the question box for card 1..3 |
| `Esc` | Close the active prompt |
| Click card | Ask a follow-up about that item |
| Drag card | Reposition it |

## Privacy and cost

Every scan sends a JPEG of the **active monitor** to the endpoint you configure. That may include passwords, private messages or financial data on screen. Read [PRIVACY.md](PRIVACY.md) before using it on sensitive screens.

- No analytics, no telemetry, no Spectra server.
- The local session cache (`.session_cache.json`) stores text only, for up to 1 hour.
- Each scan is one vision request billed by your provider. Cost depends on the model and image size.

## Known limitations

- **X11 only.** Wayland screen capture and global shortcuts need a different implementation.
- **HiDPI scaling** may offset cards from their targets.
- **Prompt injection:** text visible on screen is untrusted input to the model.
- No single-instance lock: running twice registers duplicate hotkeys.
- The overlay creates several topmost windows; some window managers may flicker or steal focus.

## Roadmap

- [ ] Wayland support (XDG Desktop Portal + `grim`)
- [ ] Tray icon, pause/private mode, configurable hotkey UI
- [ ] Local models via Ollama
- [ ] AppImage packaging
- [ ] English prompt / i18n
- [ ] Cost guard and request debounce
- [ ] Integration tests for the overlay

## Demo mode

For screenshots and videos, demo mode renders canned cards and a canned follow-up without calling a model:

```bash
SPECTRA_DEMO=1 ./run.sh
```

## Demo video

The hero video on the site is rendered from a real recording of the app running in demo mode.

- `tools/demo_stage.py` — staged 1920×1080 X11 screen used for the recording.
- `video/` — Remotion composition (`Hero`, 1920×1080, 30 fps, 20 s).
- `docs/hero.mp4` / `docs/hero.webm` — rendered output.

```bash
cd video
npm install
npx remotion render src/index.ts Hero out/hero.mp4 --codec=h264
```

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
