---
name: imagegen-openai
description: Generate and edit images with OpenAI GPT Image models through a configurable OpenAI-compatible provider. Use for raster images, GPT Image 2.6 SVG or animated GIF generation, complexity control, reference composition, masked edits, outpainting, transparent assets, markup, streaming previews, conversational image iteration, and asynchronous batches on compatible models. Discover available models before submission.
---

# ImageGen OpenAI

## Connect and discover

- Read `IMAGEGEN_OPENAI_API_BASE_URL` (default `https://api.openai.com/v1`) and `IMAGEGEN_OPENAI_API_KEY` from the execution environment. The base is complete: trim trailing slashes and append endpoint paths without inserting another `/v1`. Invalid or empty overrides fail without switching providers. Configuration declares inputs; the host supplies values. Never put the key in prompts, JSON, commands, or output; ask for configuration through settings if missing.
- Use the dependency-free Python 3.8+ helper (`<skill-dir>` is this directory):

```bash
python3 <skill-dir>/scripts/imagegen.py models
```

- Fetch the provider’s current list before every new generation, edit, Responses request, or batch submission, including explicit model requests. Live submission refreshes discovery again. Stop on discovery failure or an absent selected ID. Saving an existing response and managing an existing batch do not require discovery.
- Retain every returned model. Names and annotations are hints, not proof of modalities or endpoint support. For unfamiliar IDs, verify the provider’s endpoint and request schema before submitting; never use paid trial requests to discover capabilities or enforce a hardcoded allowlist. Preserve exact IDs, including namespaces or snapshots.
- Responses requires **both** the mainline model and image tool model to appear in the live list. Additionally verify the mainline model’s documented support for the image generation tool: listing alone is insufficient. Never hardcode a mainline default or use an image-only model in its place.

## Choose the model and route

Respect an explicit available user choice after checking capability compatibility. For Images requests, prefer GPT Image 2.6 Sunburst for detailed compositions and precise edits, or GPT Image 2.6 Flare for fast iteration. The exact IDs are `gpt-image-2.6-sunburst` and `gpt-image-2.6-flare`; do not invent a bare `gpt-image-2.6` alias. Retain 2.5/2/1.5 for documented compatible workflows. This is task guidance, not an availability list, price ranking, or visual-quality guarantee. Other listed models remain selectable after documentation checks. Explain the choice briefly.

| Task | Route |
| --- | --- |
| New image from text; transparent output | `generate` → Images generations |
| Global transformation, multiple reference images, local mask edit, canvas extension/outpainting | `edit` → Images edits |
| Transparent PNG drawing/annotation overlay for GPT Image 2.5/2.6 | `edit` with `markup`; never combine with `mask` |
| SVG vector graphic or animated GIF with GPT Image 2.6 | `generate` only; no streaming or edits; read format constraints below |
| Conversational iteration, earlier image tool calls, `previous_response_id` | `responses` → Responses with one explicit image generation tool |
| Partial previews | `stream: true`; Images top-level `partial_images`, Responses tool-level `partial_images` |
| Asynchronous independent requests | `batch-submit`, then `batch-status` and `batch-download` |
| Recover already-returned images | `save`; no new generation |
| Upload a reusable reference or a file too large for a JSON data URL | `upload` → Files with `purpose=vision`; no generation or model discovery |

Read [references/api.md](references/api.md) for the **2.6 update verified 2026-11-05**, the earlier-family matrix, schemas, and recovery. For 2.6, use `quality: auto|low|medium|high` and optional `complexity: low|medium|high` (provider default `high`); these control different things. Do not infer `xhigh`/`max` or raster size limits from 2.5. Omit `input_fidelity` for 2/2.5/2.6. The helper rejects known 2.6 models in Responses and Batch because support is not established by the checked documentation; use a separately selected compatible model for those routes, never silently substitute.

SVG/GIF require `generate`, without streaming, partial previews, or compression. SVG requires `n: 1`; optional `svg.model`/`svg.reasoning` need author-model access and documented compatibility, and the author ID is also discovered before submission. GIF uses `frame_count` (helper range 2–16, default 9) and `frame_duration_ms` (20–2000, default 200); see the reference for conflicting official limits and provider-specific frame/total-pixel budgets. Default to `size: auto` for GIF. SVG/GIF are output-only; raster edit inputs remain PNG/JPEG/WebP. Inspect SVG rendering or GIF playback as appropriate before delivery; signature/XML checks alone do not verify visual content or animation.

## Prepare and submit

Execute this helper through the host’s registered command tools (use `run_skill_command` when available). Reading this skill does not register a provider-native `image_generation` tool. Use the helper’s `responses` command for that API route; do not substitute an undeclared native tool. A returned base64 image is not delivered until it has been saved and inspected.

Edits accept `--transport auto|json|multipart` (default `auto`). Auto chooses multipart when every source and mask/markup is a local path or data URL; it chooses JSON when any reference uses HTTPS or `file_id`. This is a local choice before submission, not endpoint discovery or a fallback retry. Use `--transport json` for providers requiring the newer JSON schema; use multipart for gateways requiring uploaded image bytes. Multipart sends `image` for one source and `image[]` for multiple sources; a gateway requiring repeated `image` fields can use `--multipart-image-field image`. Check the selected transport in `--dry-run`. Multipart rejects remote/file-ID references locally and never downloads or uploads references implicitly. A failed request never triggers a second submission with another encoding.

Describe the requested subject, composition, style, exact text, and intended use. For edits, inspect the source and specify what to change and preserve. Actually pass reference images; a text description does not count as image input. Default to one PNG image with automatic size/quality unless the task needs explicit settings. Transparency needs PNG/WebP. Do not advertise adjustable high-fidelity tiers for 2/2.5/2.6. For focused 2.6 edits consider low complexity; dense text or complex relationships may benefit from high complexity, with more latency and potential unwanted changes.

Write UTF-8 JSON without BOM. All three synchronous commands share this interface:

```bash
python3 <skill-dir>/scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 <skill-dir>/scripts/imagegen.py edit --json edit.json --output-dir /absolute/path/outputs
python3 <skill-dir>/scripts/imagegen.py responses --json responses.json --output-dir /absolute/path/outputs --timeout 300
```

All three accept `--dry-run` and `--timeout`. Dry runs validate locally without a key, network, discovery, or output writes; they do not establish access. Edits accept 1–16 `images` references and optional `mask` or `markup`, each using exactly one of `image_url`, `file_id`, or the helper’s local `path` extension. Paths resolve against the request JSON’s directory. Responses accepts native input plus a local `{ "type": "input_image", "path": "source.png" }` extension converted to a data URL. Require explicit top-level `model` and tool `model`; the helper defaults `tool_choice` to `{ "type": "image_generation" }`.

For Batch, read the reference before submission. Use standard JSONL `custom_id`/`method`/`url`/`body` requests, a single model per file, at most 50,000 requests and 200 MB. Submit with `batch-submit --jsonl requests.jsonl --output-dir ...`, inspect with `batch-status --id ...`, retrieve with `batch-download --id ... --output-dir ...`. Use `batch-cancel --id ...` only when the user explicitly requests cancellation. Do not promise a particular discount or provider turnaround beyond the documented `24h` completion window.

Responses `input_image_mask` also accepts a helper-local `{ "path": "mask.png" }` reference. In Batch bodies, supported local paths resolve against the JSONL directory. Before masked/markup edits, inspect source and overlay for matching oriented dimensions. The helper checks local markup pixels for transparency, but remote references and EXIF orientation require inspection. For a local/data-URL source with an Images mask, prepare matching PNG files; non-PNG source input is locally rejected.

Synchronous multipart edits send image bytes without the JSON data-URL character limit; the per-file size limit still applies. For a reusable reference or larger input on a JSON-only route, use `upload --file /absolute/path/source.png --output-dir ...` and pass the returned ID as `file_id`. Upload accepts PNG/JPEG/WebP under 50 MiB, supports `--dry-run`/`--timeout`, saves `file.json`, and does not generate images or discover models. See the reference for the separate guide and JSON limits.

## Inspect, recover, and deliver

- Preserve the run’s request, response metadata, `response.json`, final images, and `manifest.json`. Streaming also records `events.jsonl` and `partial-...` previews; completion saves final `response.json`. Previews are not final outputs. Batch download retains raw `output.jsonl` and `error.jsonl` and associates saved images with `custom_id`.
- View final images by their returned absolute paths. Check content, edit boundaries, text, transparency, encoding, and image count. Masking is guidance, not a pixel-exact guarantee. Deliver previews, selected models, and material limitations; metadata and filenames do not prove appearance.
- No automatic retries, provider switches, model fallback, or replacement of missing outputs. Incomplete/failed streams, incomplete Responses, and timeouts may have incurred charges: keep artifacts, report status/request ID, and investigate before any new submission.
- On mixed/incomplete Responses, recover completed final image calls with `save` and report `complete: false` and failed calls; do not claim the entire request succeeded. Local/data markup receives actual PNG transparency decoding; remote references and orientation still need inspection. See reference limits before large inputs or batch downloads.
- Recover native Images or Responses outputs without another generation:

```bash
python3 <skill-dir>/scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/outputs
```

`save` needs no key or discovery; retain sibling response metadata for tracing. When a recovered Responses image model is unknown, keep image `model: null`; do not substitute the top-level mainline model or `mainline_model`. Compatible URL outputs may require network download; they never receive the API key and redirects are not followed. Do not claim live API or visual verification when only dry runs or mock checks were performed.
