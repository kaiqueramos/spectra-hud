# Privacy

Spectra HUD is a local application. There is no Spectra server, no account and no telemetry.

## What is captured

On every scan, the **active monitor** (the one under the mouse cursor) is captured as a JPEG image, downscaled to a maximum dimension of 1600 px.

## Where it goes

The image is sent over HTTPS to the endpoint configured in `SPECTRA_BASE_URL`, together with the system prompt and a short session summary. That endpoint is a third-party provider chosen by you. Its own privacy policy and retention rules apply.

If you use the default endpoint, read the provider's terms. If you point `SPECTRA_BASE_URL` to a local server (for example, Ollama with a vision model), the image never leaves your machine.

## What is stored locally

- `.env` — your API key and settings (plaintext in v0.1).
- `~/.local/state/spectra-hud/session.json` — up to 10 recent events: detected context, card labels, insights, questions and answers. Text only, no images. Mode 600. Expires after 1 hour of inactivity.
- No logs are written by default; console output only.

## How to remove local data

```bash
rm ~/.local/state/spectra-hud/session.json
```

To revoke access, delete or rotate the key at your provider and remove `.env`.

## Sensitive screens

v0.1 has **no redaction and no pause mode**. Do not trigger a scan while a password manager, banking app, medical record or private conversation is on screen. Quit Spectra when screen sharing.

## Legal

You are the controller of the data you choose to capture. The model provider is a separate controller/processor under its own terms. If you process personal data of third parties, ensure you have a legal basis under LGPD/GDPR.
