# Providers

Spectra talks to any **OpenAI-compatible** endpoint that accepts an image in
`messages[].content[]` (`image_url` with a data URL).

## Presets

| Preset | Base URL | Model | Key |
|---|---|---|---|
| OpenCode Go | `https://opencode.ai/zen/go/v1` | `deepseek-v4.1-flash` | OpenCode Go |
| OpenCode Zen | `https://opencode.ai/zen/v1` | `deepseek-v4.1-flash-free` | OpenCode |
| CommandCode | `https://api.commandcode.ai/provider/v1` | `deepseek/deepseek-v4.1-flash` | CommandCode |
| Ollama | `http://localhost:11434/v1` | `qwen2.5vl:7b` (example) | any string (`ollama`) |
| Custom | your URL | your model | your key |

Model IDs are provider-specific. The same model can have different IDs on
different gateways.

## Vision test

The command center's **Testar visão** sends a 128×128 image split red/blue and
asks the model to name the two colors. It only passes when the response
mentions both. A text-only model fails this test.

## Ollama (local)

```bash
ollama pull qwen2.5vl:7b
# or another vision model, e.g. llava
```

Then choose **Ollama (local)** in the command center. No key is required; the
app sends `Bearer ollama`. The screenshot never leaves the machine.

## Free vs paid

- OpenCode Zen has a free model, but the account quota can return
  `FreeUsageLimitError` (HTTP 429). The app shows an actionable message.
- OpenCode Go needs an active subscription/key.
- CommandCode, OpenAI and other gateways bill per token.

Spectra never ships a key. The key is stored in the system keyring (or a 600
fallback file) and is sent only to the configured base URL.

## Custom endpoint

Requirements:

1. `POST {base_url}/chat/completions`
2. `Authorization: Bearer <key>` (the header is sent even for local endpoints)
3. `messages` with `content: [{type:"text"}, {type:"image_url"}]`
4. A response with `choices[0].message.content`

If your endpoint uses a different path or auth header, open an issue with the
provider docs.
