# OpenWorkgraph Skills

[简体中文](README.zh-CN.md)

Official skill repository for OpenWorkgraph. Skills retain OpenAI and agents/skills compatibility and include an English fallback `README.md`, localized READMEs when applicable, and `config.json` for configuration declarations.

| Skill | Purpose |
| --- | --- |
| [OpenWorkgraph Skill Creator](skills/openworkgraph-skill-creator/README.md) | Create, update, or convert skills for OpenWorkgraph. |
| [VideoGen H3](skills/videogen-h3/README.md) | Generate MiniMax H3 videos, regenerate eligible outputs at 2K, and download results. |
| [ImageGen OpenAI](skills/imagegen-openai/README.md) | Generate and edit images, use masks/markup and streaming, iterate through Responses, and submit batches with live model discovery. |
| [Make PDF](skills/make-pdf/README.md) | Turn mixed source materials into a complete LaTeX document and compiled PDF. |

Skills live in `skills/<skill-name>/`. See the creator's [packaging reference](skills/openworkgraph-skill-creator/references/packaging.md) and [configuration format](skills/openworkgraph-skill-creator/references/configuration.md). Configuration format v1 is a new repository contract; application integration has not been verified.

To maintain your own collection, follow [Create your own OpenWorkgraph skills repository](docs/create-your-own-skills-repository.md).
