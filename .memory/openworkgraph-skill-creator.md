# OpenWorkgraph skill creator

## Requirements and decisions

- The owner requested a creator based on OpenAI skill-creator that supports new skills and conversion of generic OpenAI/agents/skills-compatible skills.
- Required product additions: English fallback `README.md`, localized README files such as `README.zh-CN.md`, and configuration declarations.
- No existing configuration field schema was supplied or found in the local ProjectWorkgraph source search. The owner subsequently required `config.json` exclusively; do not substitute `env.example`.
- Defined repository format v1: `version` and an `environment` declaration array. Each input has exact runtime name, English label/description, required/secret flags, optional non-secret default and translations. Secret defaults are forbidden; names must be unique.
- This is a new repository contract. Application parsing and environment injection have not been verified or implemented in this task.
- New repository skills use `skills/<skill-name>/` and English/Simplified Chinese READMEs by default; explicit user location/language choices take precedence. Conversion preserves workflows, resources, attribution, policies, and runtime variable names.

## Implementation map

- `skills/openworkgraph-skill-creator/SKILL.md`: discovery and create/update/convert workflows.
- `skills/openworkgraph-skill-creator/references/packaging.md`: README and conversion requirements, validation checklist.
- `skills/openworkgraph-skill-creator/references/configuration.md`: authoritative configuration field semantics and conflict handling.
- `skills/openworkgraph-skill-creator/references/config.schema.json`: JSON Schema for format v1.
- `skills/openworkgraph-skill-creator/scripts/validate_config.py`: dependency-free configuration validator; rejects duplicate JSON keys/names and secret defaults, never prints input values.
- Skill and root `README.md` / `README.zh-CN.md`: human documentation and repository discovery.
- Creator `config.json`: version 1 with no environment inputs. `agents/openai.yaml` provides interface metadata with automatic discovery left at its default.

## Validation

- Upstream `quick_validate.py` passed using locally cached PyYAML via `uv run --offline --with pyyaml`; no dependency download was needed.
- Empty and populated configuration fixtures passed. Thirteen invalid configuration/diagnostic cases were rejected, including duplicate variables/keys, unknown fields, secret defaults, malformed JSON, invalid names/locales, and non-standard numbers.
- CLI non-mutation and local Markdown link checks passed. Schema field coverage was checked; a full JSON Schema validator was unavailable in the local cache.
- No OpenWorkgraph application runtime validation performed. Next integration work must consume the declared contract and verify display, localization, and injection.
