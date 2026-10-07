# 自建 OpenWorkgraph 技能仓库教程

[English](create-your-own-skills-repository.md) · [仓库首页](../README.zh-CN.md)

本教程从零创建一个独立维护的 Git 仓库 `openworkgraph-skills`，添加一个可用技能，验证技能包，并发布到自己的 Git 远程仓库。仓库名称只是示例，可以自行修改。

教程遵循本仓库的[打包约定](../skills/openworkgraph-skill-creator/references/packaging.md)和[配置格式 v1](../skills/openworkgraph-skill-creator/references/configuration.md)。应用端的仓库加载、配置显示、语言选择和环境变量注入尚未验证；发布仓库不代表 OpenWorkgraph 已能安装或运行其中的技能。

## 1. 准备工具

需要 Git、用于配置校验的 Python 3，以及支持下列 Shell 命令的终端，例如 macOS/Linux 上的 Bash 或 Zsh。发布时还需要 Git 托管账户及目标仓库的推送权限。通过 Agent 创建或调用技能时，需要支持 `SKILL.md` 的 Agent。

```bash
git --version
python3 --version
```

选择一个尚不存在 `workgraph-skills-template` 和 `openworkgraph-skills` 的父目录，以下步骤在同一个终端中执行。

## 2. 初始化独立仓库

以本仓库作为创建器及校验脚本的来源，把创建器复制到一个新仓库中，后续只维护自己需要的技能。

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

如果已有源仓库的本地副本，可跳过克隆，把复制命令中的 `../workgraph-skills-template` 替换为它的路径。复用内容时保留复制的 MIT 许可证和版权声明；引入其他技能时，也需检查并保留其许可证与署名。

添加下文的示例技能后，目录结构如下：

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

`docs/` 用于仓库教程和维护说明。Agent 指令放在各技能的 `SKILL.md` 中；按需添加 `scripts/`、`references/`、`assets/` 或 `agents/openai.yaml`，无需创建空资源目录。

## 3. 添加第一个技能

技能名称使用小写字母、数字和单个连字符，不以连字符开头或结尾，长度小于 64 个字符。目录名必须与 frontmatter 的 `name` 一致。

下面的示例用于汇总本地项目文档，无需 API Key 或额外脚本。在新仓库根目录执行：

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

`README.md` 是英文回退文档，`README.zh-CN.md` 提供简体中文说明；其他语言使用 `README.<language-tag>.md`。不同语言版本的功能、依赖、配置和示例应保持一致。每个技能都需要 `config.json`，没有配置时使用空 `environment` 数组。

后续创建技能时，先通过 Agent 支持的技能加载方式启用复制的创建器，再给出明确需求，例如：

```text
使用 $openworkgraph-skill-creator 创建一个汇总本地 CSV 文件的技能。
保存到本仓库的 skills/csv-summary，提供英文、简体中文 README 和
config.json，并在创建后验证技能包。
```

转换现有技能时，指定源目录和目标目录，并要求保留原工作流、资源、许可证和配置消费者。仅复制目录不会自动向所有 Agent 注册技能，应使用实际 Agent 支持的加载或安装机制。

## 4. 按需声明配置

如果某个技能确实需要读取 API Key，可以使用下列声明。`EXAMPLE_API_KEY` 是虚构输入，并非 `project-summary` 或创建器所需配置。

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

变量名必须与运行时消费者一致，且不能重复。标签和描述默认使用英文。仅特定模式需要的输入使用 `required: false`，并在描述及 README 中说明使用条件。`default` 如果存在，必须是字符串；敏感输入禁止设置默认值。

配置文件存放声明，不存放真实凭据。`secret: true` 提示消费者遮蔽输入，不代表加密或存储功能。声明变量不会自动设置进程环境变量；运行值需通过执行环境或经过验证的应用集成提供。配置声明统一使用 `config.json`，不要生成 `env.example` 作为替代。迁移现有配置前，请阅读[字段说明与转换规则](../skills/openworkgraph-skill-creator/references/configuration.md)。

## 5. 校验并完善仓库文档

在新仓库根目录执行：

```bash
python3 skills/openworkgraph-skill-creator/scripts/validate_config.py skills/openworkgraph-skill-creator/config.json
python3 skills/openworkgraph-skill-creator/scripts/validate_config.py skills/project-summary/config.json
```

校验器检查配置字段、重复变量名/键以及敏感输入默认值，不负责验证 YAML frontmatter、注册技能或执行技能工作流。发布前还需检查：

- 每个技能具有非空的 `SKILL.md`、英文 `README.md`、有效的 `config.json` 和所需翻译。
- Frontmatter 包含非空 `name` 与 `description`，名称与目录一致。
- 本地链接和资源路径可解析；新增或修改的辅助脚本通过代表性输入验证。
- 配置声明、运行时消费者和两版 README 的变量名与依赖一致。
- 引入内容保留许可证和署名，没有跟踪凭据或私有运行文件。`.gitignore` 不会移除已经被 Git 跟踪的文件。

创建仓库级 `README.md` 和 `README.zh-CN.md`，介绍技能集合、适用用户和使用要求，并将每个技能链接到对应 README。例如英文索引：

```markdown
| Skill | Purpose |
| --- | --- |
| [Project Summary](skills/project-summary/README.md) | Summarize local project documentation. |
| [OpenWorkgraph Skill Creator](skills/openworkgraph-skill-creator/README.md) | Create or convert skills. |
```

中文索引使用中文描述及以 `README.zh-CN.md` 结尾的链接，两份根 README 互相链接。仓库维护指南可按需放入 `docs/`。

## 6. 发布与维护

在 Git 托管平台创建一个空仓库，不要预先生成 README 或许可证。将下列 `YOUR_ACCOUNT` 替换为 GitHub 用户名或组织名；使用其他平台时，改用平台提供的远程地址。在新仓库根目录执行：

```bash
git status --short
git add README.md README.zh-CN.md LICENSE .gitignore skills
# 纳入自行添加的文档。
git add docs
git diff --cached --check
git diff --cached
git commit -m "Initialize OpenWorkgraph skills repository"
git remote add origin https://github.com/YOUR_ACCOUNT/openworkgraph-skills.git
git push -u origin main
```

提交前检查暂存区差异。认证方式和仓库可见性由 Git 托管平台管理。

更新技能时，同步修改指令、配置、受影响资源和两版 README，再执行相关校验，并保持根目录技能索引最新。如需标记发行版本，可在验证后创建并推送 Git 标签；本目录约定不强制要求标签。

在应用中使用时，应针对实际 OpenWorkgraph 版本确认仓库导入机制、支持的目录结构、配置版本、语言回退和环境变量注入。验证加载及一次代表性调用后，再宣称仓库通过了应用测试。本教程完成的是遵循本地打包约定的仓库。
