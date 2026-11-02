# ImageGen OpenAI

[简体中文](README.zh-CN.md)

Generate raster images from text with OpenAI GPT Image models through OpenAI or an OpenAI-compatible provider. The skill fetches the provider's model list before use, chooses a suitable model, saves the returned images, and guides the agent to inspect them before delivery.

The agent instructions describe `gpt-image-2.5-sunburst` (highest capability and precision), `gpt-image-2.5-flare` (fast everyday generation), `gpt-image-2` (strong earlier-generation option), and `gpt-image-1.5` (previous-generation fallback). Models absent from this table remain selectable when returned by the provider; known suitable models get default preference. Explicit user choices take precedence. Availability is never inferred from the table.

## Requirements and configuration

- Python 3.8+ with the standard library; no SDK installation required.
- A provider supporting Bearer authentication, `GET /models`, and `POST /images/generations`.
- Configure these environment inputs through your skill host or execution environment:

| Variable | Required | Default |
| --- | --- | --- |
| `IMAGEGEN_OPENAI_API_BASE_URL` | No | `https://api.openai.com/v1` |
| `IMAGEGEN_OPENAI_API_KEY` | Yes for discovery/generation | None; secret |

Supply the complete API base, including `/v1` if your provider requires it. Trailing slashes are removed; no extra version segment is inserted. An explicitly empty or invalid address fails. Obtain the API key from your chosen provider and configure it without pasting it into chat or committing it. These are the only declared settings; the agent selects a model from the live catalog.

`config.json` uses repository configuration format v1 and declares inputs without storing secret values. Host loading and environment injection must be verified in the actual OpenWorkgraph installation.

## Use

Example requests to the agent:

> Use imagegen-openai to create a watercolor fox illustration, with no text, and choose a suitable available model.

> Use imagegen-openai with gpt-image-2.5-sunburst to generate a detailed product poster.

The helper can also be run directly from this skill directory:

```bash
python3 scripts/imagegen.py models
```

Create `request.json` with an exact ID returned by that command:

```json
{
  "model": "gpt-image-2.5-flare",
  "prompt": "A watercolor red fox reading under an oak tree, no text.",
  "size": "1024x1024",
  "quality": "medium"
}
```

```bash
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs
```

Dry runs need no key and perform no network requests or file writes. They validate parameters without checking availability. Live generation refreshes the provider list again immediately before submitting; absent models or failed discovery prevent submission. Model annotations are hints, so unfamiliar models need provider documentation or capability metadata.

Each live run creates a unique `imagegen-*` subdirectory containing `request.json`, the full `response.json`, a `response-meta.json` sidecar with the selected model and request ID, image files, and `manifest.json` with absolute paths and available response metadata. Keep the sidecar beside the response to preserve tracing during recovery. Defaults are one PNG image and provider-selected automatic size/quality. Parameters and source links are in [references/api.md](references/api.md). The helper checks file signatures; the agent must view outputs to verify their appearance.

If saving an image fails after a successful response, recover without generating again:

```bash
python3 scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/outputs
```

## Limits

The helper supports non-streaming text-to-image generation. Image-input editing, masks, and the Responses API are not implemented. Custom providers must use a compatible response schema. Official GPT Image returns base64; compatible URL responses are downloaded without the API key. Redirects are not followed, and responses over 256 MiB are rejected.

No automatic retries, provider switching, or model fallback occurs. A timed-out generation may still be billed; investigate before another submission. Default generation timeout is 300 seconds, adjustable with `--timeout`. No credential is needed to save a stored response, although URL results require network access.

Model guidance was verified on 2026-11-02; OpenAI schedules `gpt-image-1.5` retirement for 2026-12-01. Compatible providers may differ. Always use their current catalog and documented capabilities.
