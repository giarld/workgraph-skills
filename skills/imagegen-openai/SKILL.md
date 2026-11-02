---
name: imagegen-openai
description: Generate images using OpenAI GPT Image models through a configurable OpenAI-compatible provider. Fetch available models before use and choose by quality, speed, and task needs. Use for text-to-image requests, illustrations, posters, and other raster assets.
---

# ImageGen OpenAI

## Connect and discover

- Read `IMAGEGEN_OPENAI_API_BASE_URL` (default `https://api.openai.com/v1`) and `IMAGEGEN_OPENAI_API_KEY` from the execution environment. The base is complete: remove trailing slashes, append endpoint paths, and never insert another `/v1`. Empty or invalid overrides fail without switching providers.
- Authenticate with `Authorization: Bearer <key>`. Never put the key in commands, prompts, request JSON, or output. If missing, ask the user to configure it in the skill settings or execution environment, without asking them to paste the value into chat. `config.json` declares inputs; the host supplies their values.
- Fetch this provider's current model list **before every new generation**, including explicit model requests. Saving an existing response is exempt. Use the dependency-free Python 3.8+ helper (`<skill-dir>` is this directory):

```bash
python3 <skill-dir>/scripts/imagegen.py models
```

This calls `GET /models`, retains every returned model, and annotates known families and likely image candidates. An image-like ID is a discovery hint, not proof of image output: standard model listings do not declare modalities. Use provider documentation or capability metadata for unfamiliar IDs. Do not discard models just because their names lack `image`.

Stop on discovery failure; do not claim a cached or hardcoded catalog is current. The generation command refreshes the list again immediately before submission and requires the exact selected ID to be present.

## Choose the model

Choose from the fetched IDs. Respect an explicit user choice when available. Otherwise prefer the known models below according to the task. These are capability tiers and selection guidance, not measured scores or guaranteed provider pricing.

| Known model | Relative capability and tradeoff | Prefer for |
| --- | --- | --- |
| `gpt-image-2.5-sunburst` | Highest capability tier among these models; emphasizes precise editing and demanding visual control. | Quality-first final assets and tasks where precision matters more than latency. |
| `gpt-image-2.5-flare` | High-quality everyday tier; the speed-oriented 2.5 variant. Do not assume it is the cheapest. | General generation, drafts, and fast iteration; first choice for an unspecified everyday task when available. |
| `gpt-image-2` | Strong earlier-generation option with flexible dimensions and high-fidelity image input support. | A capable fallback when suitable 2.5 models are unavailable or the user's provider/requirements favor it. |
| `gpt-image-1.5` | Previous-generation instruction-following baseline, lower priority for demanding new work. | Explicit requests, established workflows, or fallback when newer suitable known models are unavailable. |

- **The table is not an allowlist.** Image-generation models returned by the provider but absent from the table are lower-priority candidates by default, never prohibited. Select one when the user requests it, its documented capabilities better fit, or no suitable known model is available. Do not invent its quality, speed, price, or limits from its name. Image-output metadata alone does not establish endpoint compatibility: check that an unfamiliar model accepts `/images/generations` and the request schema before using this helper.
- Dated snapshots of a known family can use that family's guidance. A provider-prefixed ID may be annotated using its final path segment; always send the full original ID. Do not silently replace an exact requested model or pin a snapshot that was not returned.
- Availability comes from the provider; these notes do not guarantee access. As checked on 2026-11-02, OpenAI schedules `gpt-image-1.5` retirement for 2026-12-01. A compatible provider may have a different lifecycle; inspect its current listing and errors.
- Prefer a short task-specific explanation of the model choice. Do not require the user to choose a model for every request.

Model descriptions and API details: [references/api.md](references/api.md), including official sources verified on 2026-11-02. Read it when choosing dimensions, quality options, or handling provider differences.

## Prepare and generate

Write a UTF-8 JSON request using the selected provider ID and the user's visual requirements. Describe subject, composition, style, intended use, and exact quoted text when relevant. Do not add text, branding, or other content the user did not request. Default to one image, PNG output, and automatic size/quality unless the task calls for explicit choices. Use `low` for quick drafts; reserve the 2.5-only `xhigh`/`max` options for justified quality needs. Transparent output needs PNG or WebP.

```json
{
  "model": "gpt-image-2.5-flare",
  "prompt": "A watercolor illustration of a red fox reading under an oak tree, warm autumn colors, no text.",
  "n": 1,
  "size": "1024x1024",
  "quality": "medium",
  "output_format": "png"
}
```

The example model is illustrative: replace it with an ID actually returned by the provider.

```bash
python3 <skill-dir>/scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 <skill-dir>/scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs
```

- Dry runs validate locally without a key, discovery, network traffic, or output files; they do not prove model availability.
- Live generation calls `POST /images/generations` only after fresh model discovery. Unknown models are accepted if listed; only recognized families receive family-specific parameter checks. The helper handles non-streaming text-to-image requests. Image-input editing, masks, and Responses API workflows are outside this helper's scope; do not pretend an input image was used by describing it in text.
- Each invocation creates a new `imagegen-*` directory under the output directory. It saves `request.json` before submission, then `response-meta.json` (selected model/request ID) and `response.json` before image retrieval, followed by images and `manifest.json`. Preserve these files until the task is delivered. The progress line gives the run directory if later work fails.
- No POST retries or automatic model fallback. On timeout, submission may have succeeded and incurred a charge; investigate provider records before another generation. On authentication, quota, moderation, or parameter errors, address the cause first. Keep progress updates during long calls (default request timeout: 300 seconds).

## Inspect and deliver

Use the returned absolute image paths to view the actual results and check composition, legibility, requested background, and format. Compare the returned image count with the request and report missing outputs without automatically submitting replacements. Deliver image previews plus the model used and any material limitation. Do not label a filename or provider metadata as visual verification.

If decoding or a compatible provider's URL download fails after generation, recover from the saved response instead of generating again:

```bash
python3 <skill-dir>/scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/outputs
```

`save` makes no generation request or model-discovery call and needs no API key; it may download image URLs present in that response. Keep the sibling `response-meta.json` to preserve the original model and request ID across recovery. Official GPT Image returns base64; URL responses are a compatibility fallback and never receive the API key. Redirects are not followed. Expired or redirecting URLs need a fresh direct URL from the provider; keep the original response and use a copy for changed URLs. Recovery may still fail and is not a reason to regenerate automatically. The JSON result reports saved files and response metadata without printing image base64. Do not claim a paid live test when only dry runs or mock-provider checks were performed.
