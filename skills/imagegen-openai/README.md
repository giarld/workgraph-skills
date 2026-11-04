# ImageGen OpenAI

[简体中文](README.zh-CN.md)

Generate and edit raster images through OpenAI or an OpenAI-compatible provider. Workflows include text-to-image, global restyling, multiple reference images, masked edits and outpainting, transparent assets, GPT Image 2.5 markup overlays, streaming previews, Responses multi-turn iteration, and asynchronous Batch requests.

The agent discovers live models before submission and checks their documented capabilities. Sunburst is suited to editing precision; Flare to fast everyday generation. Available older or unfamiliar models remain selectable after endpoint/schema verification. No model name, listing, or quality setting guarantees a particular visual result.

## Requirements and configuration

- Python 3.8+, standard library only; no SDK installation.
- Bearer authentication and `GET /models`, plus the endpoint needed for the task: Images generations/edits, Responses, or Files and Batches. A compatible provider may implement only some routes.
- Configure environment inputs in the skill host or execution environment:

| Variable | Required | Default |
| --- | --- | --- |
| `IMAGEGEN_OPENAI_API_BASE_URL` | No | `https://api.openai.com/v1` |
| `IMAGEGEN_OPENAI_API_KEY` | For live provider requests | None; secret |

Use the complete API base, including `/v1` when required. The helper removes trailing slashes without adding another version segment. Empty or invalid overrides fail without provider switching. Configure the key through settings; do not paste it into chat or commit it. These are the only declared settings; models are selected from the live catalog.

`config.json` declares repository format v1 inputs without storing values. The key is conditionally required for live requests, so its declaration has `required: false`. Local dry runs and saving a stored response need no key. Saving compatible URL output can still require network access. Host parsing/environment injection must be verified in the actual OpenWorkgraph installation.

## Use

Example agent requests:

> Use imagegen-openai to generate a transparent watercolor fox, with streaming previews.

> Edit this room using the attached furniture references; preserve the layout. Use the mask for the chair, or a separate GPT Image 2.5 markup overlay to indicate changes.

> Continue editing the previous image through Responses, using a listed mainline model with documented image generation tool support.

> Prepare a Batch of 20 independent image requests, then inspect its status and download the results when ready.

From this skill directory:

```bash
python3 scripts/imagegen.py models
```

Create UTF-8 JSON without BOM. Replace the example model with an exact returned ID whose endpoint capabilities match the request:

```json
{
  "model": "gpt-image-2.5-flare",
  "prompt": "A watercolor red fox reading a book, isolated on a transparent background, no text.",
  "size": "1024x1024",
  "quality": "medium",
  "background": "transparent",
  "output_format": "png",
  "stream": true,
  "partial_images": 2
}
```

```bash
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs
python3 scripts/imagegen.py edit --json edit.json --output-dir /absolute/path/outputs
python3 scripts/imagegen.py responses --json responses.json --output-dir /absolute/path/outputs --timeout 300
```

All three request commands accept `--dry-run` and `--timeout`. Dry runs validate locally without a key, network calls, discovery, or output writes; they do not establish model access. Live submission refreshes the model list and stops if discovery fails or any selected ID is absent.

Edits use native `images: [{image_url: ...}, {file_id: ...}]` references (1–16 images), plus the helper’s `{path: ...}` local extension. `mask` and `markup` use the same reference format, are mutually exclusive, and target the first source image. Local paths resolve against the request JSON. A markup overlay must be a transparent PNG with matching oriented dimensions and is **2.5-only**.

Responses requires an explicit top-level mainline `model` and exactly one `image_generation` tool with explicit `model`. Both are checked against the live list; additionally verify the mainline model’s documented tool support. Native input supports image URLs/file IDs and earlier `image_generation_call` context; `previous_response_id` carries conversational state. The helper converts local `{type: "input_image", path: ...}` into a data URL and defaults `tool_choice` to `{type: "image_generation"}`. Its tool schema has `input_image_mask` and **no markup field**.

Read the [API reference and 1.5/2/2.5 capability matrix](references/api.md) before choosing settings. In particular, `xhigh`/`max` and markup are 2.5-only; 1.5 has fixed sizes while 2/2.5 allow constrained custom dimensions; GPT Image 2 transparency is preview. `input_fidelity` is adjustable on 1.5 and must be omitted for 2/2.5. Unknown listed models require documented endpoint/schema verification before submission.

The Responses `input_image_mask` also supports a local `{path: ...}` reference. Before using masks or markup, inspect real transparency and oriented source/overlay dimensions. The helper only checks file signatures and readable PNG headers/alpha/dimensions; it does not fully decode images, confirm transparent pixels, or verify EXIF orientation. For Images masks, non-PNG local/data-URL source images are locally rejected; prepare matching PNG source and mask.

For reusable references or images/masks too large for a JSON data URL:

```bash
python3 scripts/imagegen.py upload --file /absolute/path/source.png --output-dir /absolute/path/uploads --dry-run
python3 scripts/imagegen.py upload --file /absolute/path/source.png --output-dir /absolute/path/uploads
```

`upload` accepts PNG/JPEG/WebP under 50 MiB, supports `--timeout`, and uploads through multipart `/files` with `purpose=vision`. It saves the returned File object in `file.json`; use its `id` as a native `file_id`. It does not generate images or discover models. The guide’s <50 MB source/mask requirement and the JSON `image_url` maximum of 20,971,520 characters are separate limits; see the reference before preparing large inputs.

## Outputs and recovery

Each live request preserves request JSON, response metadata, final `response.json`, images, and a manifest with absolute paths. Streaming also records `events.jsonl` and `partial-...` previews. The completed response is saved for recovery; previews are not final images. The agent must view final outputs to check appearance, transparency, text, and requested edits.

Save an existing native Images or Responses response without generating again:

```bash
python3 scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/recovered
```

Keep sibling response metadata for tracing. There are no automatic retries, provider/model fallbacks, or replacement requests for missing images. Incomplete responses, failed/interrupted streams, and timeouts require investigation; a submission may already have incurred a charge. Compatible image URL downloads receive no API key and do not follow redirects.

## Batch

Official Batch documentation explicitly supports GPT Image 2.5 image generation/edit endpoints; do not assume equivalent support for older models. Responses Batch also requires a documented Batch-capable mainline model and compatible image tool. Use a single model and endpoint per JSONL file, unique `custom_id` values, standard `method`/`url`/`body` fields, and at most 50,000 requests / 200 MB. Local image/mask/markup paths resolve against the JSONL directory and are converted before upload; both original and expanded JSONL must fit the limit. Do not stream Batch requests.

```bash
python3 scripts/imagegen.py batch-submit --jsonl requests.jsonl --output-dir /absolute/path/batches --endpoint /images/generations --dry-run
python3 scripts/imagegen.py batch-submit --jsonl requests.jsonl --output-dir /absolute/path/batches --endpoint /images/generations
python3 scripts/imagegen.py batch-status --id batch_returned_id
python3 scripts/imagegen.py batch-download --id batch_returned_id --output-dir /absolute/path/batch-results
```

`--endpoint` is optional and accepts `/images/generations`, `/images/edits`, or `/responses`. Submission discovers all models before multipart upload of the prepared JSONL with `purpose=batch` and creation of a batch with the `24h` completion window. Download retains raw `output.jsonl`/`error.jsonl` and associates images with `custom_id`; result order is not input order. Cancel only on an explicit user request with `batch-cancel --id ...`. No batch discount or universal provider support is promised.

Official source verification: **2026-11-04**. Full request examples, mask/file-size versus URL-character limits, and source links are in [references/api.md](references/api.md).
