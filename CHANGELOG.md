# Changelog

## Unreleased

- New 18 s hero loop and 24 s launch film built in Remotion, with real command center captures, kinetic type and an original soundtrack.
- Site: launch film section with captions, new hero video/poster and updated social card.

## 0.2.1 — 2026-10-25

Security patch.

- Pillow 13.0.0 (fixes image-decoding CVEs and resource-exhaustion issues).
- Remotion toolchain forces zod 4.6.7; `npm audit` reports 0 vulnerabilities.
- No API keys or secrets in the repository, history, logs or shell history.

## 0.2.0 — 2026-10-25

Command center polish.

- Frameless Spectra titlebar with drag, hide and close; no WM decoration in dark or light themes.
- Custom switches, pill buttons, live theme cards and icon controls.
- Telemetry panel (latency, tokens, cost) and system panel (provider, keyring, consent, privacy, cache).
- Microanimations: scanline, pulsing LED, switch transitions; toggle in the interface section.
- Interface languages: Portuguese (BR), English and Spanish; the model answers in the selected language.
- Editable YAML configuration (`config.yaml`) for every setting, with YAML > JSON precedence, Reload YAML / `Ctrl+R`, and invalid-YAML protection.
- Immediate private-mode toggle and language/theme persistence.
- 61 unit tests.

## 0.1.0 — 2026-10-24

First public release.

- Global scan hotkey with toggle and scanning indicator.
- Vision model returns up to 3 insights with optional `box_2d` anchoring.
- Draggable cards, click-to-ask follow-up, global command bar.
- Target highlight is a single left bar; no box and no numbered badge.
- Command center (`Ctrl+Alt+C`) with provider presets, base URL, model, keyring, consent, pause, blocklist, hotkeys and pricing.
- First-run wizard, explicit LGPD consent and a red/blue vision test.
- Tray icon (AppIndicator) with scan, pause and quit.
- Cancel an in-flight scan from the indicator or the scan hotkey.
- Latency, token usage and optional cost readout.
- Private mode and window-title blocklist.
- Local models via Ollama.
- Safe side-column fallback when the model's box is unreliable.
- Rotating local logs and actionable 401/403/429/404 messages.
- 10 themes (5 dark, 5 light), live preview in the command center, `Ctrl+T` cycle.
- Command-center typography: Share Tech Mono for display, FiraCode NF for mono, Ubuntu for body, with DejaVu fallback; higher-contrast dim labels.
- 1-hour sliding session memory.
- Multi-monitor capture on X11.
- Bring-your-own-key configuration via `.env` or environment variables.
- Apache 2.0 license.
- 57 unit tests.
- Fail-fast on Wayland with a clear message.
- Single-instance lock.
- Thread-safe follow-up results (no Tk calls from worker threads).
- Session cache in XDG state with mode 600; reads no longer renew the TTL.
- Cards clamped to the monitor; insight text capped.
- X11 display handle closed after focus requests; `xdotool` has a timeout and Xlib fallback.
- Default scan hotkey is `Ctrl+Alt+Space` to avoid IDE autocomplete.
- Prompt-injection guard in the system prompt.
- `SPECTRA_DEMO=1` renders canned cards for screenshots and videos (no model calls).

Known limitations: X11 only, the base system prompt is Brazilian Portuguese (the response language is overridden), no pixel redaction, no packaging yet.
