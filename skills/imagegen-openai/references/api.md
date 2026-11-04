# Image generation API reference

Official sources were checked on **2026-11-04**. Provider model listings establish availability, not capability. Verify the documented endpoint, schema, model features, and account access before submitting. Never probe an unfamiliar model with paid requests to find out whether it works.

## Routes and commands

Append paths to the configured complete API base; do not add a second version segment. Bearer authentication applies to provider API requests. Discovery uses `GET /models` and retains all returned IDs; there is no model allowlist or mainline-model default. Model-like names and annotations are advisory.

| Command | Endpoint / purpose |
| --- | --- |
| `models` | `GET /models`; inspect the live catalog |
| `generate` | `POST /images/generations`; text to image |
| `edit` | `POST /images/edits`; global edit, references, mask, outpainting, or markup |
| `responses` | `POST /responses`; conversational image tool use |
| `save` | Decode a stored native Images or Responses response without generation |
| `upload` | `POST /files`, multipart `purpose=vision`; obtain a reusable image file ID without model discovery |
| `batch-submit` | Discover models, upload JSONL to `POST /files`, then `POST /batches` |
| `batch-status` / `batch-download` / `batch-cancel` | Inspect, download, or explicitly cancel an existing batch |

The examples below run from the skill directory. Replace example image-model IDs with exact IDs from the live catalog. Replace Responses main-model placeholders with a listed mainline model whose official model page confirms image generation tool support; the tool model must also be listed. GPT Image models belong in `tools[0].model`, not in the Responses top-level `model`.

```bash
python3 scripts/imagegen.py models
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --timeout 300
python3 scripts/imagegen.py edit --json edit.json --output-dir /absolute/path/outputs
python3 scripts/imagegen.py responses --json responses.json --output-dir /absolute/path/outputs
```
`generate`, `edit`, and `responses` require `--json` and `--output-dir` and accept `--dry-run` and `--timeout` (seconds; default 300). Dry runs need no key and perform no discovery, network request, or file write; local file references are still checked. Live submission refreshes the catalog and checks every selected model. Discovery failure stops submission. For Responses, presence in the catalog does not establish tool support: check documentation as well.

The `models` output includes local `skill_capabilities` annotations for recognized families. These describe the helper’s known profiles, not provider-certified capabilities; unrecognized listed models remain selectable after endpoint/schema verification.

## Capability matrix: check before submission

This describes official GPT Image families, not a provider availability guarantee. Dated snapshots and provider namespaces retain their exact listed IDs. Consult provider documentation for aliases and other models; do not infer features from an ID alone.

| Capability | GPT Image 1.5 | GPT Image 2 | GPT Image 2.5 Sunburst / Flare |
| --- | --- | --- | --- |
| Text generation; global image edits; reference composition; mask-guided inpainting/outpainting | Supported through Images endpoints | Supported through Images endpoints | Supported through Images endpoints |
| Quality | `auto`, `low`, `medium`, `high` | Same as 1.5 | Adds `xhigh` and `max`; these are 2.5-only |
| Sizes | `auto`, `1024x1024`, `1536x1024`, `1024x1536`; no arbitrary-size assumption | Custom sizes within limits below | Custom sizes within limits below |
| Transparent background | Supported with PNG/WebP | **Preview**, including `gpt-image-2-2026-04-21` | Supported, including `2026-09-08` snapshots |
| `input_fidelity` for image inputs | `low` / `high`; optional, default `low` | **Omit**; not an adjustable setting | **Omit**; do not advertise adjustable fidelity tiers |
| `markup` transparent overlay | Not supported | Not supported | **Images edits only**; cannot combine with mask |
| Images streaming / partial previews | Available where the endpoint/model supports streaming | Same | Supported; see streaming section |
| Responses image tool | Verify selected tool model and mainline-model tool support | Same | Same; image model is explicit in the tool |
| Batch `/images/generations` and `/images/edits` | No support inferred from 2.5 documentation | No support inferred from 2.5 documentation | Official Batch guide explicitly supports both variants and `2026-09-08` snapshots |

For **2 and 2.5**, both edges must be multiples of 16 and no more than 3840 pixels, aspect ratio must be between 1:3 and 3:1, and total pixels must be 655,360–8,294,400. Resolutions above `2560x1440` are experimental. `3840x2160` and `2160x3840` are documented 4K examples, not permission to exceed edge/pixel limits. A valid example is `1536x864`; do not apply these custom-size rules to 1.5.

Sunburst is documented for editing precision; Flare for fast everyday generation. These descriptions do not guarantee exact text, composition, identity preservation, price, or visual quality. Choose settings for the actual task, inspect results, and report limitations.

## Images generation JSON

| Field | Values / behavior |
| --- | --- |
| `model` | Required by the helper; exact currently listed ID with documented endpoint support |
| `prompt` | Nonempty text, maximum 32,000 characters |
| `n` | Integer 1–10; default 1; multiple outputs are one synchronous request, not Batch |
| `size` / `quality` | See matrix; omitted/`auto` lets the provider select |
| `output_format` | `png` (default), `jpeg`, `webp` |
| `background` | `auto`, `opaque`, `transparent`; transparency needs PNG/WebP and model support |
| `output_compression` | Integer 0–100, only JPEG/WebP; API default 100 |
| `moderation` | `auto` or `low`; leave omitted unless needed |
| `safety_identifier` | Optional privacy-preserving end-user identifier, at most 128 characters; hash personal identifiers |
| `user` | Deprecated compatibility field; prefer `safety_identifier` |
| `stream` | Boolean; default false |
| `partial_images` | Integer 0–3 for streaming; default 0 |

Use native GPT Image fields, not legacy `style` or `response_format`. GPT Image returns base64 images. Describe style in the prompt. A nonempty `safety_identifier` takes precedence over deprecated `user`. Request acceptance for unfamiliar models requires their provider’s documented schema.

Example `request.json`, including a transparent asset and streaming previews:

```json
{
  "model": "gpt-image-2.5-flare",
  "prompt": "A watercolor red fox reading a book, isolated on a transparent background, no text.",
  "n": 1,
  "size": "1024x1024",
  "quality": "medium",
  "background": "transparent",
  "output_format": "png",
  "stream": true,
  "partial_images": 2
}
```
For a compressed opaque asset use `output_format: "jpeg"` or `"webp"`, `output_compression: 80`, and `background: "opaque"`. Change 2.5 quality to `xhigh` or `max` only when the task warrants it. Never carry those quality values into a 1.5/2 request.

## Images edits: native references and local extension

The helper sends JSON, not the SDK’s multipart `image[]` syntax. Use required `images` (1–16 references) plus `prompt` and explicit `model`. Output/streaming fields follow the Images table. `input_fidelity` is available only for supported older models such as 1.5; omit it for 2/2.5.

Every reference in `images`, `mask`, or `markup` must have exactly one of:

- `{ "image_url": "https://example.com/image.png" }`: an HTTPS source.
- `{ "image_url": "data:image/png;base64,..." }`: a data URL.
- `{ "file_id": "file-..." }`: an uploaded image file accessible to the provider.
- `{ "path": "assets/source.png" }`: helper-only extension; converted to a data URL before submission.

All local `path` values resolve relative to **the request JSON file**, not the shell working directory. Do not combine keys or send `path` to the API. Native file IDs/URLs are not proof that source dimensions or alpha were checked locally. Ordinary source images and masks receive file-signature and readable PNG header/dimension/alpha-marker checks; local markup additionally receives the PNG decoding checks below. The helper does not apply/check EXIF orientation or decode remote references. Before submitting, inspect the source and overlay, confirm matching dimensions after orientation, and prepare corrected files if needed.

Global transformation and multi-reference composition, `edit.json`:

```json
{
  "model": "gpt-image-2.5-sunburst",
  "images": [
    { "path": "assets/room.png" },
    { "image_url": "https://example.com/chair.png" },
    { "file_id": "file-lamp-reference" }
  ],
  "prompt": "Place the chair from image 2 and lamp from image 3 into the room in image 1. Preserve the room layout and window positions.",
  "size": "1536x1024",
  "quality": "high",
  "output_format": "png"
}
```
For a global restyle, keep one source and change the prompt, for example: “Restyle this room as a watercolor illustration while preserving the layout.” Input references must actually be submitted.

### Masked edit and outpainting

Add `mask` to an edit to guide changes to the **first** source image. It must have an alpha channel; fully transparent areas identify regions to edit. The guide requires source and mask to have matching format/dimensions and be **less than 50 MB**. The helper requires local/data-URL masks to be PNG; when a mask is present it locally rejects a non-PNG local/data-URL first source. Prepare matching PNG source and mask before submission. Native file IDs/HTTPS URLs still require the agent to verify format and dimensions. Mask guidance is prompt-based and does not guarantee exact shape or untouched pixels elsewhere.

```json
{
  "model": "gpt-image-2.5-sunburst",
  "images": [{ "path": "assets/room.png" }],
  "mask": { "path": "assets/room-mask.png" },
  "prompt": "Replace the masked chair with a blue armchair. Preserve the surrounding room.",
  "output_format": "png"
}
```
For **outpainting**, prepare a larger source canvas with the original positioned inside it and a same-size alpha mask whose new area is transparent. Submit them through `edit`, choose a supported output size, and prompt for extending the scene into that area. Do not invent an `outpaint` endpoint or guarantee exact pixel preservation.

The JSON reference schema independently limits **each `image_url` to 20,971,520 characters**, including a data URL’s prefix/base64 expansion. A local file under 50 MB can still exceed that encoded limit. Use `upload` below and pass its returned ID as `file_id`, or resize/re-encode as appropriate. Do not apply an obsolete blanket 4 MB mask limit or equate the guide’s file limit with the JSON character limit.

### Upload references and masks without generating

```bash
python3 scripts/imagegen.py upload --file /absolute/path/source.png --output-dir /absolute/path/uploads --dry-run
python3 scripts/imagegen.py upload --file /absolute/path/source.png --output-dir /absolute/path/uploads --timeout 300
```

`upload` accepts a local PNG/JPEG/WebP file **under 50 MiB** (helper upload limit), validates it, and sends multipart `POST /files` with `purpose=vision`. This helper limit is separate from the guide’s <50 MB source/mask requirement and the JSON URL-character limit; satisfy the requirements for the eventual edit as well. Upload requires the provider key but **no model discovery**, generates no image, and saves the returned File object in `file.json`. Its `id` can be used as `{ "file_id": "file-returned-id" }` for references or masks; markup files must still meet the transparent-PNG/dimension requirements. `--dry-run` checks locally without a key, network, or output writes. Do not upload to a different provider or claim that uploading proves edit-model compatibility.

### GPT Image 2.5 markup

For local/data-URL markup specifically, the helper decodes PNG pixels (including Adam7 and palette transparency), checks CRCs, and rejects fully opaque overlays before submission. Decoded scanlines are limited to 64 MiB; larger inputs can be uploaded and referenced by file ID after independent inspection. Remote/file references and EXIF orientation still require inspection. Ordinary source images and masks receive the lighter checks described above.

`markup` is a transparent PNG overlay used to point, draw, or annotate on the first source image. It must match that image’s dimensions **after orientation** and contain transparent pixels. Available only for GPT Image 2.5 Images edits. `markup` and `mask` are mutually exclusive; markup is not a binary edit mask.

```json
{
  "model": "gpt-image-2.5-sunburst",
  "images": [{ "path": "assets/room.png" }],
  "markup": { "path": "assets/room-annotations.png" },
  "prompt": "Use the arrows on the overlay to locate the chair. Replace it with a blue armchair and remove the annotation marks from the final image.",
  "output_format": "png"
}
```
## Responses: mainline model plus image tool

Send native Responses input, not an Images request wrapped in a tool. The helper requires explicit top-level `model` and **exactly one** `image_generation` tool with explicit `model`. Both IDs must be returned by current discovery. Verify the mainline model’s official tool support separately. A model being listed, newer, or accepting image inputs does not alone prove it can call the image generation tool. The helper defaults `tool_choice` to `{ "type": "image_generation" }` when omitted.

The current official tool schema contains:

| Tool field | Meaning |
| --- | --- |
| `type` | `image_generation` |
| `model` | Explicit image model; not the top-level mainline model |
| `action` | `auto` (default), `generate`, `edit`; `edit` needs an image in context |
| `background`, `size`, `quality`, `output_format`, `output_compression`, `moderation` | Same documented output meanings; family constraints still apply |
| `partial_images` | Integer 0–3; Responses `stream` stays at the top level |
| `input_image_mask` | Native mask object using `file_id` or `image_url`; the schema describes `image_url` as a base64 mask. The helper also accepts `{ "path": "mask.png" }` and converts it to a data URL |
| `input_fidelity` | Supported older-model setting only; omit for 2/2.5 |

There is **no `markup`, `images`, `mask`, `n`, `prompt`, or `stream` field in this tool schema**. Put textual/image content in top-level `input`. Put `safety_identifier` at request level, not inside the tool. Use the Images edits route if markup is needed.

Example `responses.json` (replace the main-model placeholder before running):

```json
{
  "model": "<listed-main-model-with-image-generation-tool-support>",
  "input": [{
    "role": "user",
    "content": [
      { "type": "input_text", "text": "Turn this room into a watercolor illustration, preserving the layout." },
      { "type": "input_image", "path": "assets/room.png" }
    ]
  }],
  "tools": [{
    "type": "image_generation",
    "model": "gpt-image-2.5-sunburst",
    "action": "edit",
    "quality": "high",
    "output_format": "png",
    "partial_images": 2
  }],
  "tool_choice": { "type": "image_generation" },
  "stream": true
}
```
The local `{ "type": "input_image", "path": "..." }` extension resolves against the request JSON and becomes native `{ "type": "input_image", "image_url": "data:..." }`. Native image input also accepts HTTPS/data URLs with `image_url` or uploaded `file_id`. Keep other native input content and documented Responses options in their original structure.

For a masked conversational edit, put `"input_image_mask": { "path": "assets/room-mask.png" }` or a native `{ "file_id": "file-mask" }` reference in the tool, and pass the source via `input`. The helper converts the local mask path relative to the request JSON. Do not copy the Images `mask` key into the tool. Inspect source/mask format, transparency, and dimensions before submission; local header checks do not replace visual/decoded-image verification.

For a subsequent turn use `previous_response_id` and another native input while still explicitly selecting both models and the image tool:

```json
{
  "model": "<listed-main-model-with-image-generation-tool-support>",
  "previous_response_id": "resp_previous",
  "input": "Make the chair blue and retain the rest of the scene.",
  "tools": [{ "type": "image_generation", "model": "gpt-image-2.5-sunburst", "action": "edit" }]
}
```
Alternatively pass earlier `image_generation_call` output items in native `input` context, including the image-call ID as documented. Preserve the actual returned IDs/result rather than inventing an image reference. `previous_response_id` and explicit image-call context are alternative official ways to carry image history; an ordinary text description alone does not carry the image.

## Streaming, artifacts, recovery, and incomplete responses

Images generation/edit streaming uses top-level `stream: true` and `partial_images`. Images SSE emits `image_generation.partial_image` / `image_generation.completed` or the corresponding `image_edit.*` events. Responses uses top-level `stream: true` and tool-level `partial_images`; preview events are `response.image_generation_call.partial_image` and completion is `response.completed`. Zero partial images still allows a final streaming event. Requested preview count is an upper bound: a final image can arrive before all previews.

A run preserves `request.json`, `response-meta.json`, completed `response.json`, final images, and `manifest.json` with absolute output paths and available metadata. Streaming adds `events.jsonl` and `partial-...` preview files. Keep event logs separate from the final response. Provider metadata is not independent evidence of visual quality. Task artifacts may contain prompts, image bytes, IDs, and signed URLs; do not commit them to the skill package.

Native Images output uses `data[].b64_json`; native Responses output uses `output[]` items with `type: "image_generation_call"` and base64 `result`. `save` handles both:

```bash
python3 scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/recovered
```
Recovery needs no key or model discovery. Keep the sibling `response-meta.json` for original model/request-ID tracing. In a native Responses response, top-level `model` identifies the mainline model, not the image tool model. If the image model cannot be established from saved tool metadata or the image call, report image `model: null` (unknown); preserve any `mainline_model` separately and never substitute it for the image model. Compatible Images URL responses are downloaded without Bearer authentication; redirects are not followed. Actual image signatures determine PNG/JPEG/WebP extensions.

A partial preview, missing output, `response.incomplete`, `response.failed`, stream interruption, or timeout is not a successful final generation. Preserve available artifacts and report status, sanitized error, request ID, and run path. Do not automatically retry, switch provider/model, or generate replacements. A timed-out submission may already have succeeded and incurred a charge. Recover available final bytes before considering a new request; `save` cannot turn a partial preview into a completed response.

Recovery distinguishes completed image calls from overall Responses completion. If some image calls failed, successful final image bytes are still saved and the manifest records complete=false plus failed_image_generation_calls. A live request reports failure for that mixed result; offline save can recover its successful images. A completed response.output_item.done image is persisted as an incomplete recoverable response even if the connection ends before response.completed. Partial previews remain previews.

## Batch: asynchronous Images or Responses requests

The official Batch guide explicitly supports GPT Image 2.5 Sunburst/Flare and their `2026-09-08` snapshots on `/v1/images/generations` and `/v1/images/edits`. Do not assume 1.5/2 Batch image support. Batch `/v1/responses` additionally requires a documented Batch-capable mainline model and compatible image generation tool; verify both, not just their presence in the model catalog. Never infer a provider’s Batch support from its synchronous endpoints.

Each UTF-8 JSONL line is a standard request with unique `custom_id`, `method: "POST"`, `url`, and endpoint `body`. A file targets one endpoint and a **single model**; for Responses keep the same mainline model and explicit image tool model throughout. At most **50,000 requests / 200 MB** per input file. The helper reuses edit/Responses preparation: local image, mask, and markup `path` extensions are supported and resolve relative to **the JSONL file’s directory** before conversion to native data URLs. Both input and expanded JSONL must fit the upload limit; native HTTPS/file-ID references can avoid base64 expansion. Do not stream Batch requests.

Example `requests.jsonl`, each request on exactly one line:

```jsonl
{"custom_id":"fox-1","method":"POST","url":"/v1/images/generations","body":{"model":"gpt-image-2.5-flare","prompt":"A watercolor fox reading, no text.","size":"1024x1024","quality":"medium"}}
{"custom_id":"fox-2","method":"POST","url":"/v1/images/generations","body":{"model":"gpt-image-2.5-flare","prompt":"A watercolor fox sleeping, no text.","size":"1024x1024","quality":"medium"}}
```
```bash
python3 scripts/imagegen.py batch-submit --jsonl requests.jsonl --output-dir /absolute/path/batches --endpoint /images/generations --dry-run
python3 scripts/imagegen.py batch-submit --jsonl requests.jsonl --output-dir /absolute/path/batches --endpoint /images/generations
python3 scripts/imagegen.py batch-status --id batch_returned_id
python3 scripts/imagegen.py batch-download --id batch_returned_id --output-dir /absolute/path/batch-results
```
The optional CLI `--endpoint` accepts `/images/generations`, `/images/edits`, or `/responses`; native official JSONL `url` values include `/v1` as shown. Submission validates the file, discovers **all** referenced models before upload, uploads the prepared JSONL as `input.jsonl` via multipart `/files` with `purpose=batch`, then creates a batch at `/batches` using its `input_file_id` and `completion_window: "24h"`. This is asynchronous, not a promise that every request succeeds. Do not promise a batch price or discount from a generic Batch headline; consult current image-specific pricing and provider terms when asked.

Inspect status by ID. Download available provider output/error files and retain raw `output.jsonl` and `error.jsonl`; decode successful native Images/Responses bodies and associate saved images with `custom_id`. Output order can differ from input order. Report per-request errors, missing or expired items, and incomplete responses without automatic resubmission. Existing-batch status/download do not require model rediscovery.

Only if the user explicitly requests cancellation, run `python3 scripts/imagegen.py batch-cancel --id batch_returned_id`. Cancellation can take time and completed work may remain in the results; inspect status and available output rather than assuming all requests were undone.

## Official sources

Batch result files are downloaded in chunks without the single-response 256 MiB total limit. Each JSONL result line has a 256 MiB processing limit; oversized or malformed lines are reported while later valid lines continue. Interrupted downloads retain a .partial file and byte counts in the manifest, without automatic retry. Batch input is split only at physical LF record boundaries, preserving Unicode line separator characters inside prompts.

Verified **2026-11-04** against these official pages:

- [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation): route selection, output settings, dimensions, masks, limitations, streaming, earlier-model fidelity.
- [Generate image](https://developers.openai.com/api/reference/resources/images/methods/generate): native Images fields.
- [Edit image](https://developers.openai.com/api/reference/resources/images/methods/edit): JSON references, 16-image limit, markup, URL character limits.
- [Image generation tool](https://developers.openai.com/api/docs/guides/tools-image-generation): image context, tool choice, multi-turn and streaming behavior.
- [Create response](https://developers.openai.com/api/reference/resources/responses/methods/create): native input and the separate image tool schema.
- [Files API](https://developers.openai.com/api/reference/resources/files): file uploads and reusable file IDs.
- [GPT Image 2.5 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst): model modalities, image endpoints, tool use and Batch support.
- [Batch guide](https://developers.openai.com/api/docs/guides/batch): supported image models/endpoints, single-model files, 50,000 requests / 200 MB, 24h window, upload/download lifecycle.

The helper adds local-path conversion, preflight discovery, validation, artifact saving, and recovery. Those are local contracts, not new API parameters or a claim that every compatible provider implements the entire OpenAI feature set.
