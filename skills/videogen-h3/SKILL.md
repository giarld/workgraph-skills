---
name: videogen-h3
description: Generate videos through the MiniMax H3 API from text, frame images, or multimodal references; regenerate eligible H3 768P outputs at 2K, query asynchronous tasks, and download results.
---

# VideoGen H3

## Connection

- Default API base: `https://api.minimax.cn/v2`. If `VIDEOGEN_H3_API_BASE_URL` is set, use it with trailing `/` removed. Supply the complete V2 base URL; do not append `/v2` twice. Empty or invalid overrides are errors, without silent fallback.
- Read `VIDEOGEN_H3_API_KEY` from the environment and authenticate with `Authorization: Bearer <key>`. Never print the key or write it into request JSON or skill files. If missing, ask the user to set it in the agent's execution environment; do not request the key text.
- Default to `MiniMax-H3`, `768P`, and 5 seconds; use `16:9` for text-only generation. State these defaults. Use `MiniMax-H3-Max` when the user explicitly selects the fast variant; see the reference for its specifications.
- Requests follow MiniMax's official V2 schema. Validate custom endpoint compatibility at runtime; do not automatically switch endpoints or credentials after failure.

## Choose a mode

Read the relevant schema, examples, and media limits in [references/api.md](references/api.md), then write a JSON request file.

1. **Text-to-video:** one `text` item with an explicit aspect ratio.
2. **Image-to-video:** `text` plus a first frame, last frame, or both; set the ratio to `adaptive`.
3. **Multimodal reference-to-video:** `text` plus any nonempty combination of reference images, videos, and audio. Do not mix references with first/last frames.
4. **Video regeneration:** use the separate `video_regeneration` endpoint to regenerate eligible H3 768P outputs at 2K. This is not general video editing or arbitrary upscaling. Task-ID mode requires allowlist access; source-video mode requires the exact final generation prompt and all original reference media.

Media may use public URLs, `mm_file://` references, or data URIs. Confirm custom endpoint support for platform file references at runtime. Local paths are not URLs. Convert small local files to data URIs; for large files, use accessible URLs supplied by the user without uploading to third parties on your own. Check formats, dimensions, duration, frame rate, and request size against the reference. The script validates JSON structure but does not inspect remote media.

## Execute and deliver

Use the dependency-free Python 3 helper; `<skill-dir>` is this skill's directory:

```bash
python3 <skill-dir>/scripts/h3.py create --json request.json
python3 <skill-dir>/scripts/h3.py regenerate --json regen.json
python3 <skill-dir>/scripts/h3.py query --task-id TASK_ID
python3 <skill-dir>/scripts/h3.py wait --task-id TASK_ID --timeout 900 --interval 15
python3 <skill-dir>/scripts/h3.py download --task-id TASK_ID --output /absolute/path/video.mp4
```

- Add `--dry-run` to create/regenerate commands to validate locally and print the endpoint and a summary with media omitted. This needs no key and makes no network requests.
- Record `task_id` and the request file immediately after submission. After a wait timeout, query the same task rather than creating another. Creation/regeneration POSTs are not automatically retried: a network timeout leaves submission uncertain. Investigate task records before deciding whether to create a new task to avoid duplicate charges.
- `queued` / `running` are pending. Only `succeeded` allows retrieval of `task.content.url`; stop and report errors for `failed` / `cancelled`. Waiting is bounded; maintain progress communication during long waits.
- Queries cover the last 7 days. Result URLs expire, so download promptly to the user's requested location or the current task output directory. Return an absolute-path video preview, the task ID, and actual output specifications.
- Downloads do not send the API key to the CDN. Address 401, 402, invalid parameters, or failed tasks before continuing; do not repeatedly resubmit.

Source reference verification date: 2026-10-06. Without configured credentials, perform local validation only and do not claim successful live API testing.
