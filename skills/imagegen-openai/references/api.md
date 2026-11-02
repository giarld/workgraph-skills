# Image API notes

Verified against official OpenAI documentation on 2026-11-02. Custom providers may expose fewer models, different lifecycle dates, or different supported parameters; their live listing and documentation determine actual availability.

## Endpoints and request

Append `/models` and `/images/generations` to the configured complete API base. Both use Bearer authentication. The helper does not follow redirects for authenticated requests and never falls back to another service. `GET /models` returns an object containing a `data` array of model objects with `id` strings. Standard OpenAI listings provide identity and availability metadata, not a reliable image-output capability flag. The helper also follows the common compatible-provider `has_more` / `last_id` cursor convention when present.

`POST /images/generations` accepts a JSON object. The helper supports:

| Field | Values / behavior |
| --- | --- |
| `model` | Required exact ID from the current provider list. No hardcoded model default or allowlist. |
| `prompt` | Required nonempty text, at most 32,000 characters. |
| `n` | Integer 1–10; helper default 1. More outputs may increase charges. |
| `size` | `auto` by default at the provider, or `WIDTHxHEIGHT`; see known-family limits below. |
| `quality` | `auto`, `low`, `medium`, `high`; 2.5 adds `xhigh` and `max`. Omitted means provider default. Unprofiled models may use a different nonempty quality string if documented by the provider. |
| `output_format` | `png` (helper default), `jpeg`, or `webp`. |
| `background` | `auto`, `opaque`, or `transparent`. Transparency requires PNG/WebP. |
| `output_compression` | Integer 0–100, only with JPEG/WebP. |
| `moderation` | `auto` or `low`; leave omitted unless the user/task needs a change. |
| `safety_identifier` | Optional nonempty string, up to 128 characters; never use raw personal identifiers. |

The helper rejects unsupported fields to catch mistakes before billing. Do not send legacy `response_format` or `style` to GPT Image. Describe style in the prompt. Streaming is not implemented in the helper. Image-input edits require the separate `/images/edits` endpoint and are not implemented here.

## Known-family constraints

- `gpt-image-1.5`: `auto`, `1024x1024`, `1536x1024`, `1024x1536`; quality up to `high`.
- `gpt-image-2`: flexible dimensions, both divisible by 16, aspect ratio from 1:3 to 3:1; quality up to `high`. Check the provider's current pixel/edge constraints for custom sizes.
- `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst`: same recommended standard sizes, plus custom dimensions divisible by 16, aspect ratio 1:3–3:1, neither edge over 3840 pixels, and 655,360–8,294,400 total pixels. Above `2560x1440` is experimental. Quality additionally supports `xhigh` and `max`; `auto` is the provider default.

The helper applies these family-specific checks only to exact family IDs, their `-YYYY-MM-DD` snapshots, and those IDs with a provider namespace. An unrecognized listed model remains selectable; its provider validates any model-specific limits. A listed model can still fail generation because of access, quota, endpoint compatibility, or retirement.

## Response, recovery, and failures

Official GPT Image returns `data[].b64_json`, decoded to binary files. No `response_format` field is necessary. Compatible providers sometimes return `data[].url`; the helper downloads such results without Bearer authentication, accepts only HTTP(S), and checks PNG/JPEG/WebP file signatures. Output extensions reflect the actual detected encoding.

Every live run saves the request, full successful JSON response, image files, and a manifest in a unique directory. A `response-meta.json` sidecar stores the selected model and request ID before image retrieval. The manifest includes that context, response size/quality/background/usage metadata when supplied, and absolute output paths. Recovery reads a sibling `<response-stem>-meta.json` sidecar when available and copies it into the new run directory. Without a sidecar, model identity is taken only from the response if present and the original HTTP request ID is unavailable. Provider metadata is not independent proof of actual visual quality. Stored responses can contain prompts and temporary signed image URLs; keep them with task outputs rather than committing them to the skill package.

A failed image retrieval can be resumed with `save --response ...`. Do not regenerate solely to recover bytes already returned. Requests are not automatically retried. In particular, a timed-out POST has an uncertain outcome. Report HTTP status, sanitized error details, request ID when supplied, and the saved run directory; investigate before another chargeable request.

## Sources

- [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation)
- [Create image reference](https://developers.openai.com/api/reference/resources/images/methods/generate)
- [List models reference](https://developers.openai.com/api/reference/resources/models/methods/list)
- [GPT Image 2.5 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)
- [GPT Image 2.5 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)
- [GPT Image 2](https://developers.openai.com/api/docs/models/gpt-image-2)
- [GPT Image 1.5](https://developers.openai.com/api/docs/models/gpt-image-1.5)
- [Deprecations](https://developers.openai.com/api/docs/deprecations)
