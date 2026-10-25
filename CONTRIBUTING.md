# Contributing

Thanks for taking a look. This is an early-stage project; small, focused PRs are welcome.

## Setup

```bash
git clone https://github.com/kaiqueramos/spectra-hud.git
cd spectra-hud
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
```

## Before opening a PR

- `pytest -q` must pass (61 tests today).
- Keep the change scoped; one concern per PR.
- Match the existing style (no formatter is enforced yet).
- Never commit `.env`, keys, screenshots or `.session_cache.json`.
- If you touch the overlay, describe how you tested it on X11 (window manager, resolution, scaling).

## Reporting bugs

Open an issue with: distro, session type (`echo $XDG_SESSION_TYPE`), Python version, window manager, steps to reproduce and the console output. Redact any key or personal data.

## Security

See [SECURITY.md](SECURITY.md). Do not open public issues for vulnerabilities.
