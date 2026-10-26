# Troubleshooting

## First checks

- `echo $XDG_SESSION_TYPE` must be `x11`.
- `python3 -c "import tkinter"` must work.
- Logs: `~/.local/state/spectra-hud/spectra.log`.
- Config: `~/.config/spectra-hud/config.yaml` (primary) and `config.json` (fallback); no key inside if the keyring works.

## HTTP 401 / 403

The key is invalid, expired or from another provider. Open the command center
(`Ctrl+Alt+C`), paste a new key, run **Testar visão**, save.

OpenCode Go keys can expire; the message is `api_key_expired`.

## HTTP 429

Quota/rate limit. The message `FreeUsageLimitError` means the free Zen quota is
exhausted. Switch provider/model or wait for the quota to reset.

## HTTP 404 / 400

- Model ID does not exist on that provider.
- The model is text-only and rejects image content.
- Base URL is missing or has an extra path.

Run **Testar visão**; a text-only model fails it.

## Timeout

Large screenshots + slow models. Try a faster model, a smaller monitor, or a
provider closer to you. The scan indicator has a **CANCEL** action; the same
scan hotkey also cancels.

## Wayland

Wayland runs in **beta** mode: capture via the Screenshot portal or
`grim`/`gnome-screenshot`/`spectacle`, results in a normal panel, and scans
triggered by the tray or `spectra-hud --scan` bound to a system shortcut.
There is no anchored overlay over other windows. See [WAYLAND.md](WAYLAND.md).

If capture fails, install a backend (`gnome-screenshot`, `spectacle` or `grim`)
and try again. The portal may ask for permission.

## Tray icon missing

The app uses `pystray` with AppIndicator. On GNOME, enable the
**AppIndicator** extension. If the backend is unavailable, the tray is skipped;
`Ctrl+Alt+C` still opens the command center.

## Keyring prompt / no keyring

If `keyring` cannot access Secret Service, the key falls back to
`~/.config/spectra-hud/config.json` (mode 600; YAML never stores the key). Check that the keyring daemon is
running and unlocked.

## Hotkeys do not change

Hotkeys are registered when the app starts. Save in the command center and
restart `./run.sh`.

## Card not aligned with the target

The model's `box_2d` is approximate. Spectra draws a thin bar at the target and
falls back to a side column when the box is unreliable. Drag the card if needed;
HiDPI offset is a known limitation.

## Scan blocked

The active window title matched the blocklist. Close the sensitive window or
edit the list in the command center. The scan is refused **before** capture.

## Reset

```bash
rm ~/.config/spectra-hud/config.yaml ~/.config/spectra-hud/config.json
rm ~/.local/state/spectra-hud/session.json
```

To remove the key: open the command center, clear the field and save; or remove
the `spectra-hud` entry in your keyring app.
