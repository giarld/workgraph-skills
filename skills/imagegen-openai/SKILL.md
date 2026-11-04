---
name: imagegen-openai
description: Generate and edit raster images with OpenAI GPT Image models through a configurable OpenAI-compatible provider. Use for text-to-image, reference-image composition, global or masked edits, outpainting, transparent assets, GPT Image 2.5 markup, streaming previews, conversational image iteration, and asynchronous batches. Discover available models before submission.
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

Respect an explicit available user choice after checking capability compatibility. Otherwise prefer a documented suitable model: GPT Image 2.5 Sunburst for editing precision, Flare for fast everyday generation, or 2/1.5 for compatible established workflows. This is task guidance, not an availability list, price ranking, or visual-quality guarantee. Other listed models remain selectable after documentation checks. Explain the choice briefly.

| Task | Route |
| --- | --- |
| New image from text; transparent output | `generate` → Images generations |
| Global transformation, multiple reference images, local mask edit, canvas extension/outpainting | `edit` → Images edits |
| Transparent PNG drawing/annotation overlay for GPT Image 2.5 | `edit` with `markup`; never combine with `mask` |
| Conversational iteration, earlier image tool calls, `previous_response_id` | `responses` → Responses with one explicit image generation tool |
| Partial previews | `stream: true`; Images top-level `partial_images`, Responses tool-level `partial_images` |
| Asynchronous independent requests | `batch-submit`, then `batch-status` and `batch-download` |
| Recover already-returned images | `save`; no new generation |
| Upload a reusable reference or a file too large for a JSON data URL | `upload` → Files with `purpose=vision`; no generation or model discovery |

Read [references/api.md](references/api.md) for the **1.5/2/2.5 capability matrix**, schemas, examples, input limits, streaming, batch lifecycle, and official sources verified **2026-11-04**. Check the matrix before preparing a request: `xhigh`/`max` and `markup` are 2.5-only; GPT Image 2 transparency is preview; adjustable `input_fidelity` belongs to 1.5, and must be omitted for 2/2.5. Batch image endpoints are currently documented for 2.5; do not extend that support to older models without evidence. Do not copy Images-only fields into a Responses tool.

## Prepare and submit

Describe the requested subject, composition, style, exact text, and intended use. For edits, inspect the source and specify what to change and preserve. Actually pass reference images; a text description does not count as image input. Default to one PNG image with automatic size/quality unless the task needs explicit settings. Transparency needs PNG/WebP. Do not advertise adjustable high-fidelity tiers for 2/2.5.

Write UTF-8 JSON without BOM. All three synchronous commands share this interface:

```bash
python3 <skill-dir>/scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 <skill-dir>/scripts/imagegen.py edit --json edit.json --output-dir /absolute/path/outputs
python3 <skill-dir>/scripts/imagegen.py responses --json responses.json --output-dir /absolute/path/outputs --timeout 300
```

All three accept `--dry-run` and `--timeout`. Dry runs validate locally without a key, network, discovery, or output writes; they do not establish access. Edits accept 1–16 `images` references and optional `mask` or `markup`, each using exactly one of `image_url`, `file_id`, or the helper’s local `path` extension. Paths resolve against the request JSON’s directory. Responses accepts native input plus a local `{ "type": "input_image", "path": "source.png" }` extension converted to a data URL. Require explicit top-level `model` and tool `model`; the helper defaults `tool_choice` to `{ "type": "image_generation" }`.

For Batch, read the reference before submission. Use standard JSONL `custom_id`/`method`/`url`/`body` requests, a single model per file, at most 50,000 requests and 200 MB. Submit with `batch-submit --jsonl requests.jsonl --output-dir ...`, inspect with `batch-status --id ...`, retrieve with `batch-download --id ... --output-dir ...`. Use `batch-cancel --id ...` only when the user explicitly requests cancellation. Do not promise a particular discount or provider turnaround beyond the documented `24h` completion window.

Responses `input_image_mask` also accepts a helper-local `{ "path": "mask.png" }` reference. In Batch bodies, supported local paths resolve against the JSONL directory. Before masked/markup edits, inspect source and overlay for matching oriented dimensions. The helper checks local markup pixels for transparency, but remote references and EXIF orientation require inspection. For a local/data-URL source with an Images mask, prepare matching PNG files; non-PNG source input is locally rejected.

For a reusable reference or an image/mask exceeding the JSON data-URL limit, use `upload --file /absolute/path/source.png --output-dir ...` and pass the returned ID as `file_id`. Upload accepts PNG/JPEG/WebP under 50 MiB, supports `--dry-run`/`--timeout`, saves `file.json`, and does not generate images or discover models. See the reference for the separate guide and JSON limits.

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
