# Configuration (YAML)

The command center writes an editable YAML file at:

```text
~/.config/spectra-hud/config.yaml
```

`config.json` is still written next to it for compatibility, but **YAML wins**
when both exist. Do not edit both at the same time.

## Precedence

```text
built-in defaults  <  config.json (legacy)  <  config.yaml  <  environment variables
```

`SPECTRA_API_KEY`, `SPECTRA_BASE_URL` and `SPECTRA_MODEL` override the files for
the current process.

## Full example

```yaml
# Spectra HUD — configuration
provider: commandcode
base_url: https://api.commandcode.ai/provider/v1
model: deepseek/deepseek-v4.1-flash

language: pt              # pt | en | es
theme: spectra            # any key from theme.py
animations: true          # scanline, LED pulse, switch transitions
paused: false             # true = private mode at startup

consent: true             # true records LGPD consent; false revokes it

blocklist:                # window-title terms; empty list disables it
  - 1password
  - bitwarden
  - keepass
  - lastpass
  - banco
  - nubank

hotkeys:
  scan: "<ctrl>+<alt>+<space>"
  bar: "<ctrl>+<shift>+<space>"
  center: "<ctrl>+<alt>+c"
  pause: "<ctrl>+<alt>+p"

pricing:                  # optional, USD per 1M tokens
  deepseek/deepseek-v4.1-flash:
    in: 0.0
    out: 0.0
```

## API key

The key is **not** stored in YAML. It lives in the system keyring under the
service `spectra-hud`. Use the command center to replace it, or export
`SPECTRA_API_KEY` before starting the app.

## Applying changes

1. Edit `config.yaml`.
2. In the command center, click **RECARREGAR** (or press `Ctrl+R`).
3. New **hotkeys** only take effect after restarting the app; everything else
   applies immediately.

The **YAML** button opens the file in your default editor. If the file does not
exist yet, it is created from the current settings.

## Comments

Saving from the command center rewrites `config.yaml` (header comments are kept,
but your own inline comments may be dropped). If you keep a heavily annotated
file, edit it while the app is stopped and use **RECARREGAR** instead of saving.

## Invalid YAML

If the YAML cannot be parsed, the app keeps the last valid JSON settings and the
command center shows `YAML inválido: ...`. Fix the file and reload. The app never
overwrites a YAML file on startup, so your edits are not lost.

## Security

- `yaml.safe_load` is used; arbitrary Python objects are rejected.
- Files are written with mode `600`.
- Do not put API keys or other secrets in YAML.
