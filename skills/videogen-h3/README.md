# VideoGen H3

Generate and download videos through the MiniMax H3 V2 API. Supports text-to-video, first/last-frame image-to-video, multimodal image/video/audio references, and regeneration of eligible H3 768P outputs at 2K.

## Prerequisites and configuration

- Python 3.8 or later; the helper uses only the standard library.
- API access and sufficient credits for live operations. Custom endpoints must implement the MiniMax V2 schema.
- Accessible media URLs, platform file references, or data URIs when using media inputs. Local paths cannot be submitted as URLs.

| Environment variable | Required | Purpose |
| --- | --- | --- |
| `VIDEOGEN_H3_API_KEY` | Yes for live operations | Bearer API key; not needed for local dry runs. |
| `VIDEOGEN_H3_API_BASE_URL` | No | Complete V2 base URL; defaults to `https://api.minimax.cn/v2`. Empty or invalid overrides fail. |

Configure the key in the agent's execution environment without pasting it into prompts or request files. [config.json](config.json) declares configuration inputs; it does not set environment variables or store secret values. OpenWorkgraph configuration parsing and environment injection remain unverified.

## Usage

Example agent requests:

- “Use $videogen-h3 to generate a five-second seaside sunrise video.”
- “Use $videogen-h3 to animate these first and last frames.”
- “Use $videogen-h3 with this character image, camera-motion video, and voice reference.”
- “Use $videogen-h3 to regenerate eligible task TASK_ID at 2K.”
- “Use $videogen-h3 to query TASK_ID and download the completed video.”

Defaults: `MiniMax-H3`, `768P`, 5 seconds, and `16:9` for text-only generation. The agent writes explicit request parameters; the script does not fill missing defaults. Request `MiniMax-H3-Max` explicitly for the fast variant.

For manual use, prepare JSON using [the API reference](references/api.md), then run from this skill directory:

```bash
python3 scripts/h3.py create --json request.json --dry-run
python3 scripts/h3.py create --json request.json
python3 scripts/h3.py regenerate --json regen.json
python3 scripts/h3.py query --task-id TASK_ID
python3 scripts/h3.py wait --task-id TASK_ID --timeout 900 --interval 15
python3 scripts/h3.py download --task-id TASK_ID --output /absolute/path/video.mp4
```

`--dry-run` also works with `regenerate`; it validates locally without a key or network access. See [SKILL.md](SKILL.md) for agent workflow instructions.

## Outputs and limitations

Submission returns a task ID; queries return status and, on success, a temporary video URL. Downloads return an absolute local path and do not overwrite existing files. Keep the task ID and original request file for recovery. The agent delivers a local video preview and actual output specifications.

- Queries cover the last 7 days; download successful results promptly before URLs expire.
- Regeneration is limited to eligible H3 768P generated videos. Task-ID mode needs allowlist access; source-video mode needs the exact final prompt and all original reference media.
- The helper checks JSON structure and request size, not remote media properties or every server-side constraint.
- Create/regenerate requests are not automatically retried. Investigate uncertain submissions before creating another paid task. A wait timeout can be resumed by querying the same task.
- Query/wait exit with code `1` on failed or cancelled tasks; wait uses code `2` for a polling timeout. Successful commands use code `0`.

API specifications retain the source skill's verification date of 2026-10-06. Package validation does not establish successful live API operation or application integration.

[简体中文](README.zh-CN.md)
