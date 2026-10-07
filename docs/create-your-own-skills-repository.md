# Create your own OpenWorkgraph skills repository

[简体中文](create-your-own-skills-repository.zh-CN.md) · [Repository home](../README.md)

This tutorial creates an independently maintained Git repository named `openworkgraph-skills`, adds a usable skill, validates its package, and publishes the repository to your own Git remote. The name is an example; you can choose another name.

It follows this repository's [packaging contract](../skills/openworkgraph-skill-creator/references/packaging.md) and [configuration format v1](../skills/openworkgraph-skill-creator/references/configuration.md). Application-side repository loading, configuration display, locale selection, and environment injection have not been verified. Publishing a repository does not establish that OpenWorkgraph can install or run it.

## 1. Prepare your tools

You need Git, Python 3 for configuration validation, and a terminal supporting the shell commands below, such as Bash or Zsh on macOS/Linux. To publish, you also need a Git hosting account and permission to push to the destination. An agent supporting `SKILL.md` is needed when creating or invoking skills through an agent.

```bash
git --version
python3 --version
```

Choose a parent directory where neither `workgraph-skills-template` nor `openworkgraph-skills` already exists. Run the following steps in the same terminal.

## 2. Initialize an independent repository

Use this repository as the source of the creator and its validator. Copy the creator into a fresh repository so that you can maintain only the skills you choose.

```bash
git clone https://github.com/giarld/workgraph-skills.git workgraph-skills-template
mkdir openworkgraph-skills
cd openworkgraph-skills
git init -b main
mkdir skills docs
cp -R ../workgraph-skills-template/skills/openworkgraph-skill-creator skills/
cp ../workgraph-skills-template/LICENSE LICENSE
cp ../workgraph-skills-template/.gitignore .gitignore
```

If you already have a local checkout of the source repository, skip the clone and replace `../workgraph-skills-template` in the copy commands with its path. Keep the copied MIT license and copyright notice for reused content. Inspect and preserve licenses and attribution when importing other skills too.

After adding the example below, the layout is:

```text
openworkgraph-skills/
├── README.md
├── README.zh-CN.md
├── LICENSE
├── .gitignore
├── docs/
└── skills/
    ├── openworkgraph-skill-creator/
    └── project-summary/
        ├── SKILL.md
        ├── README.md
        ├── README.zh-CN.md
        └── config.json
```

`docs/` holds repository tutorials and maintenance notes. Agent instructions belong in each skill's `SKILL.md`. Add `scripts/`, `references/`, `assets/`, or `agents/openai.yaml` only when they serve the skill.

## 3. Add your first skill

Use lowercase letters, digits, and single hyphens for the skill name, with no leading or trailing hyphen and fewer than 64 characters. The directory name and frontmatter `name` must match.

This example summarizes a local project's documentation without API keys or extra scripts. From the new repository root, run:

```bash
mkdir skills/project-summary
cat > skills/project-summary/SKILL.md <<'EOF'
---
name: project-summary
description: Summarize a local project's purpose, setup, and main entry points from its README and relevant documentation. Use when the user requests a project overview.
---

# Project Summary

1. Identify the project directory from the user's request or current workspace.
2. Read its README and only documentation relevant to purpose, setup, and entry points.
3. Summarize the purpose, documented setup commands, and main entry points in the user's language.
4. Cite local source paths for factual claims. Mark missing information as unknown instead of inventing commands or features.
5. Return the summary in the conversation unless the user requests a file. Reading documented commands does not authorize running them.
EOF

cat > skills/project-summary/README.md <<'EOF'
# Project Summary

[简体中文](README.zh-CN.md)

Summarize a local project's purpose, documented setup, and main entry points.

Requires an agent supporting SKILL.md and read access to the target project. No additional dependencies or environment variables are required.

Example: Use $project-summary to summarize the current project and cite the documentation paths.

Output: a summary in the conversation, or a file if requested. Undocumented details are marked as unknown; setup commands are not executed merely to produce a summary.
EOF

cat > skills/project-summary/README.zh-CN.md <<'EOF'
# 项目摘要

[English](README.md)

汇总本地项目的用途、文档中的启动步骤和主要入口。

需要支持 SKILL.md 的 Agent，以及目标项目的读取权限。无需额外依赖或环境变量。

调用示例：使用 $project-summary 汇总当前项目，并引用文档路径。

输出：对话中的摘要；用户要求时保存到文件。未记录的信息标为未知，不会仅为了生成摘要而执行启动命令。
EOF

cat > skills/project-summary/config.json <<'EOF'
{
  "version": 1,
  "environment": []
}
EOF
```

`README.md` is the English fallback. `README.zh-CN.md` provides Simplified Chinese documentation; additional translations use `README.<language-tag>.md`. Keep capabilities, dependencies, configuration, and examples aligned across translations. Every skill includes `config.json`, even when `environment` is empty.

For later skills, make the copied creator available using your agent's supported skill-loading mechanism, then supply a concrete request:

```text
Use $openworkgraph-skill-creator to create a skill that summarizes local CSV files.
Save it in skills/csv-summary in this repository, with English and Simplified
Chinese READMEs and config.json. Validate its package after creation.
```

To convert an existing skill, provide its source and destination and request preservation of its workflow, resources, license, and configuration consumers. Copying a directory alone does not register it with every agent; use your agent's supported loading or installation mechanism.

## 4. Declare configuration when needed

For a skill that actually consumes an API key, a declaration can look like this. `EXAMPLE_API_KEY` is a fictional input, not a requirement of `project-summary` or the creator.

```json
{
  "version": 1,
  "environment": [
    {
      "name": "EXAMPLE_API_KEY",
      "label": "API key",
      "description": "Required for requests to the example service.",
      "required": true,
      "secret": true,
      "translations": {
        "zh-CN": {
          "label": "API 密钥",
          "description": "调用示例服务时必须提供。"
        }
      }
    }
  ]
}
```

Variable names must match the runtime consumers and be unique. Labels and descriptions default to English. Use `required: false` for inputs needed only in a particular mode, and explain the condition in the description and READMEs. A `default`, when present, must be a string and is forbidden for secret inputs.

The file stores declarations, not actual credentials. `secret: true` tells consumers to mask an input; it does not encrypt or store it. Declaring a variable does not set it in the process environment. Supply runtime values through the executing environment or a verified application integration. Use `config.json` for declarations rather than generating `env.example` as a replacement. See the [field reference and conversion rules](../skills/openworkgraph-skill-creator/references/configuration.md) before migrating existing configuration.

## 5. Validate and document the repository

Run from your new repository root:

```bash
python3 skills/openworkgraph-skill-creator/scripts/validate_config.py skills/openworkgraph-skill-creator/config.json
python3 skills/openworkgraph-skill-creator/scripts/validate_config.py skills/project-summary/config.json
```

The validator checks configuration fields, duplicate names/keys, and forbidden secret defaults. It does not validate YAML frontmatter, register skills, or run their workflows. Before publishing, also check:

- Every skill has nonempty `SKILL.md` and English `README.md`, a valid `config.json`, and requested translations.
- Frontmatter has nonempty `name` and `description`; the name matches the directory.
- Local links and resource paths resolve; new or changed helpers work with representative inputs.
- Configuration declarations, consumers, and both READMEs agree on variable names and prerequisites.
- Imported licenses and attribution remain present; no credentials or private runtime files are tracked. `.gitignore` does not remove files already tracked by Git.

Create repository-level `README.md` and `README.zh-CN.md` describing your collection, intended users, and usage requirements. Link each skill to its corresponding README, for example:

```markdown
| Skill | Purpose |
| --- | --- |
| [Project Summary](skills/project-summary/README.md) | Summarize local project documentation. |
| [OpenWorkgraph Skill Creator](skills/openworkgraph-skill-creator/README.md) | Create or convert skills. |
```

In the Chinese index, use Chinese descriptions and links ending in `README.zh-CN.md`. Link the two root READMEs to each other. Add repository maintenance guides under `docs/` as needed.

## 6. Publish and maintain

Create an empty repository on your Git hosting service without pre-generating a README or license. Replace `YOUR_ACCOUNT` below with your GitHub account or organization, or use your chosen host's remote URL. Then run from the new repository root:

```bash
git status --short
git add README.md README.zh-CN.md LICENSE .gitignore skills
# Include any documentation you have added.
git add docs
git diff --cached --check
git diff --cached
git commit -m "Initialize OpenWorkgraph skills repository"
git remote add origin https://github.com/YOUR_ACCOUNT/openworkgraph-skills.git
git push -u origin main
```

Review the staged diff before committing. Authentication and repository visibility are managed by your Git host.

When updating a skill, update its instructions, configuration, affected resources, and both READMEs together, then repeat relevant validation. Keep the root skill index current. To mark a release, you may create and push a Git tag after validation; tags are optional for this layout.

For application use, confirm the repository import mechanism, supported layout, configuration version, locale fallback, and environment injection in the actual OpenWorkgraph build you use. Verify loading and a representative invocation there before describing your repository as application-tested. This tutorial establishes a repository that follows the local packaging contract.
