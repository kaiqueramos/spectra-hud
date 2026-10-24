# Changelog

## 0.1.0 — 2026-10-24

First public release.

- Global scan hotkey with toggle and scanning indicator.
- Vision model returns up to 3 insights with optional `box_2d` anchoring.
- Draggable cards, click-to-ask follow-up, global command bar.
- 1-hour sliding session memory.
- Multi-monitor capture on X11.
- Bring-your-own-key configuration via `.env` or environment variables.
- Apache 2.0 license.
- 36 unit tests.

Known limitations: X11 only, Brazilian Portuguese prompt, no redaction/pause mode,
`Ctrl+Space` conflicts with IDE autocomplete, no packaging yet.
