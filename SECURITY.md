# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's
[private security advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
for this repository.

Include: affected version, steps to reproduce, impact, and a suggested fix if you have one.

## Threat model

Spectra is a local desktop app that sends screenshots to a third-party model endpoint.

- **API key:** stored in `.env` in plaintext in v0.1. It is read at startup and sent only to `SPECTRA_BASE_URL`. Never commit `.env`; if a key leaks, revoke it at the provider immediately.
- **Screenshots:** the full active monitor is captured and sent to the configured endpoint. There is no redaction in v0.1. Treat the provider as a data processor and avoid sensitive screens.
- **Local state:** `~/.local/state/spectra-hud/session.json` stores the last 10 text events for up to one hour, mode 600. It is not encrypted.
- **Prompt injection:** any text visible on screen can influence the model's output. The app only displays text; it does not execute commands or call tools.
- **Transport:** HTTPS is verified by Python's default SSL context. A custom `SPECTRA_BASE_URL` can point anywhere, including a malicious host — only use endpoints you trust.

## Hardening checklist for users

- Use a dedicated API key with a spending limit.
- Keep `.env` with mode `600`.
- Do not run Spectra on screens with passwords, banking or medical data.
- Rotate the key if the machine is shared or the file was exposed.
