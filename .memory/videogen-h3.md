# VideoGen H3 conversion

## Requirements and decisions

- User requested copying `/Users/gxin/.codex/skills/videogen-h3/` into `skills/`, applying `openworkgraph-skill-creator`, and converting skill content to English.
- Agent instructions, API reference (including prompt examples), and interface metadata are English. Human documentation uses English fallback and Simplified Chinese localization per repository packaging rules.
- Preserved `scripts/h3.py` byte-for-byte and retained runtime environment names and automatic invocation defaults. Excluded `.DS_Store`; source directory was not edited.
- `config.json` uses repository format v1. `VIDEOGEN_H3_API_KEY` is secret, required for live operations, without a default; dry runs need no key. `VIDEOGEN_H3_API_BASE_URL` is optional, defaults to `https://api.minimax.cn/v2`, and includes Chinese UI translations.

## Implementation and documentation map

- `skills/videogen-h3/SKILL.md`: English entrypoint and operational constraints.
- `skills/videogen-h3/references/api.md`: translated source schemas, media limits, examples, and official source links. Retains source verification date 2026-10-06; no fresh online verification was performed.
- `skills/videogen-h3/scripts/h3.py`: dependency-free Python helper; Python 3.8+ (uses `Path.unlink(missing_ok=True)`).
- `skills/videogen-h3/agents/openai.yaml`: translated short description; existing display name retained.
- `skills/videogen-h3/README.md`, `README.zh-CN.md`, and `config.json`: OpenWorkgraph packaging.
- Root READMEs: added skill discovery rows, preserving existing content.
- Packaging contract: `skills/openworkgraph-skill-creator/references/packaging.md` and `references/configuration.md`.

## Validation and limitations

- Creator configuration validator and upstream skill `quick_validate.py` passed (PyYAML from offline uv cache).
- All five API reference examples passed key-free CLI dry runs, including both regeneration modes. Custom base trailing-slash normalization and rejection of an empty base passed.
- Relative Markdown links, English operational content, script compilation, and byte-for-byte script preservation checked.
- No live API calls or paid generation. OpenWorkgraph loading, configuration parsing, and environment injection remain unverified; `config.json` only declares inputs.
