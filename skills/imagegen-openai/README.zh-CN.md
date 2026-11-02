# ImageGen OpenAI

[English](README.md)

通过 OpenAI 或 OpenAI 兼容供应商，使用 GPT Image 系列模型将文字生成栅格图像。技能会在使用前拉取供应商模型列表、选择合适模型并保存图像，同时要求 Agent 在交付前查看实际产物。

技能提示词描述了 `gpt-image-2.5-sunburst`（最高能力与精度）、`gpt-image-2.5-flare`（快速日常生成）、`gpt-image-2`（能力较强的前代选择）和 `gpt-image-1.5`（上一代回退选择）。供应商返回但不在能力表里的模型仍可选择；默认优先选择已知且适合任务的模型，用户明确指定时优先遵从。能力表不代表实时可用列表。

## 前提与配置

- Python 3.8+，仅使用标准库，无需安装 SDK。
- 供应商支持 Bearer 认证、`GET /models` 和 `POST /images/generations`。
- 通过技能宿主或执行环境配置以下环境变量：

| 变量 | 是否必需 | 默认值 |
| --- | --- | --- |
| `IMAGEGEN_OPENAI_API_BASE_URL` | 否 | `https://api.openai.com/v1` |
| `IMAGEGEN_OPENAI_API_KEY` | 拉取模型和生成时必需 | 无；敏感输入 |

填写完整 API 基础地址，按供应商要求包含 `/v1`。脚本移除末尾斜杠，不重复添加版本路径；显式空值或无效地址会报错。API key 从所选供应商获取并配置，不要粘贴到聊天中或提交到仓库。仅声明这两个配置项，模型由 Agent 从实时列表中选择。

`config.json` 使用仓库配置格式 v1，仅声明输入，不存储密钥值。宿主加载和环境变量注入仍须在实际 OpenWorkgraph 环境中验证。

## 使用

向 Agent 发出的示例请求：

> 用 imagegen-openai 生成一幅水彩狐狸插画，不要文字，按任务选择当前可用的合适模型。

> 用 imagegen-openai 的 gpt-image-2.5-sunburst 生成细节丰富的产品海报。

也可以在本技能目录下直接运行脚本：

```bash
python3 scripts/imagegen.py models
```

创建 `request.json`，模型 ID 必须使用该命令实际返回的完整值：

```json
{
  "model": "gpt-image-2.5-flare",
  "prompt": "A watercolor red fox reading under an oak tree, no text.",
  "size": "1024x1024",
  "quality": "medium"
}
```

```bash
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs
```

Dry-run 无需密钥，不联网也不写入文件，仅验证参数，不确认模型可用性。在线生成会在提交前再次刷新供应商列表；模型不存在或列表获取失败时不会提交。模型注解仅为提示，陌生模型需参考供应商文档或能力元数据。

每次在线运行在输出目录下创建独立的 `imagegen-*` 子目录，保存 `request.json`、完整 `response.json`、记录所选模型及请求 ID 的 `response-meta.json`、图像文件和带绝对路径及可用响应元数据的 `manifest.json`。恢复时保留与响应同目录的元数据文件，以延续请求追踪。默认生成一张 PNG，尺寸和质量交由供应商自动选择。参数及来源见 [references/api.md](references/api.md)。脚本检查文件签名；图像外观须由 Agent 查看确认。

成功获得响应后若图像保存失败，可以恢复保存而不重新生图：

```bash
python3 scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/outputs
```

## 限制

脚本支持非流式文生图，暂未实现图片输入编辑、蒙版及 Responses API。自定义供应商须使用兼容响应结构。官方 GPT Image 返回 base64；兼容供应商返回 URL 时，脚本下载图像但不发送 API key。不跟随重定向，拒绝超过 256 MiB 的响应。

不自动重试、切换供应商或回退模型。生成超时仍可能产生费用，应先排查再决定是否重新提交。默认生成超时为 300 秒，可用 `--timeout` 调整。保存已有响应无需密钥，但 URL 产物仍需联网下载。

模型说明核实日期为 2026-11-02；OpenAI 计划于 2026-12-01 停用 `gpt-image-1.5`，兼容供应商可能有不同安排。始终以供应商实时列表和能力文档为准。
