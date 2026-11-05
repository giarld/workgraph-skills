# ImageGen OpenAI

[English](README.md)

通过 OpenAI 或 OpenAI 兼容供应商生成、编辑图像。涵盖栅格图像、GPT Image 2.6 SVG/GIF 生成、全局风格转换、多参考图合成、蒙版编辑与扩图、透明背景、GPT Image 2.5/2.6 涂鸦 markup，以及兼容模型的流式预览、Responses 多轮迭代和异步 Batch。

Agent 在提交前实时发现模型并核对能力文档。Images 请求优先选择 GPT Image 2.6 Sunburst 处理细节与精确编辑，或 GPT Image 2.6 Flare 进行快速迭代；旧模型或陌生模型在确认端点和 schema 后仍可选。模型名称、列表和质量档位均不构成视觉效果保证。

## GPT Image 2.6

Images 请求使用实时发现的 `gpt-image-2.6-sunburst` 或 `gpt-image-2.6-flare`。脚本支持 `complexity: low|medium|high`（API 默认 `high`）、markup 编辑，以及 SVG/GIF 生成。`quality` 使用 `auto|low|medium|high`，不直接继承 2.5 扩展档位。

SVG 设置 `output_format: svg`、`n: 1`；GIF 设置 `output_format: gif`，可选 `frame_count` 和 `frame_duration_ms`。两者均不支持编辑、流式或输出压缩。官方 GIF 范围有差异，脚本暂取交集：2–16 帧、每帧 20–2000 ms；预览权限和像素预算须另行核实。SVG/GIF 按实际格式保存，也可通过 `save` 恢复。完整示例见 [API 参考](references/api.md#gpt-image-26-verified-2026-11-05)。

在已核实文档明确支持前，脚本拒绝已识别的 2.6 模型用于 Responses 或 Batch；这些流程仍需单独选择兼容模型，不会自动替换。

## 前提与配置

- Python 3.8+，仅使用标准库，无需安装 SDK。
- 供应商提供 Bearer 认证、`GET /models` 和任务所需接口：Images 生成／编辑、Responses，或 Files 与 Batches。兼容供应商可能只实现部分路由。
- 通过技能宿主或执行环境配置：

| 变量 | 是否必需 | 默认值 |
| --- | --- | --- |
| `IMAGEGEN_OPENAI_API_BASE_URL` | 否 | `https://api.openai.com/v1` |
| `IMAGEGEN_OPENAI_API_KEY` | 在线请求供应商时必需 | 无；敏感输入 |

填写完整 API 基础地址，按供应商要求包含 `/v1`。脚本移除末尾斜杠，不重复添加版本路径；显式空值或无效地址会报错，不自动切换供应商。在设置中配置密钥，不要粘贴到聊天中或提交到仓库。仅声明这两个配置项，模型从实时列表中选择。

`config.json` 使用仓库配置格式 v1，仅声明输入，不保存配置值。密钥只在在线模式必需，因此声明为 `required: false`；本地 dry-run 和保存已有响应无需密钥。保存兼容供应商的 URL 产物仍可能联网。宿主解析与环境变量注入须在实际 OpenWorkgraph 安装中验证。

## 使用

向 Agent 发出的示例请求：

> 用 imagegen-openai 生成透明背景的水彩狐狸，并提供流式预览。

> 根据附带的家具参考图修改这张房间图，保留布局；用蒙版指定椅子区域，或单独用 GPT Image 2.6 的涂鸦标注图指示修改位置。

> 通过 Responses 继续编辑上一张图，选择实时可用且文档明确支持图片生成工具的主模型。

> 准备 20 个独立图像请求的 Batch，提交后检查状态并在结果就绪时下载。

在本技能目录下运行：

```bash
python3 scripts/imagegen.py models
```

以 UTF-8 无 BOM 创建请求 JSON。将示例模型替换为列表实际返回、且端点能力适合任务的完整 ID：

```json
{
  "model": "gpt-image-2.6-flare",
  "prompt": "A watercolor red fox reading a book, isolated on a transparent background, no text.",
  "size": "1024x1024",
  "quality": "medium",
  "background": "transparent",
  "output_format": "png",
  "stream": true,
  "partial_images": 2
}
```

```bash
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs --dry-run
python3 scripts/imagegen.py generate --json request.json --output-dir /absolute/path/outputs
python3 scripts/imagegen.py edit --json edit.json --output-dir /absolute/path/outputs
python3 scripts/imagegen.py responses --json responses.json --output-dir /absolute/path/outputs --timeout 300
```

三种请求命令均接受 `--dry-run` 和 `--timeout`。Dry-run 无需密钥、不联网、不发现模型、不写文件，只验证本地请求，不能证明实际可用性。在线提交前再次刷新模型列表；发现失败或任一选定 ID 不存在时停止提交。

编辑使用官方 `images: [{image_url: ...}, {file_id: ...}]` 引用数组，最多 16 张；脚本额外支持本地 `{path: ...}`。`mask` 与 `markup` 使用相同引用格式，二者互斥并作用于第一张源图。本地路径相对请求 JSON 所在目录解析。Markup 必须为带透明像素的 PNG，尺寸须与源图按方向校正后的尺寸一致，适用于 **2.5/2.6**。

Responses 须显式提供顶层主模型 `model`，以及唯一的 `image_generation` 工具及其 `model`。两个模型均检查实时列表；还须另查主模型是否明确支持图片生成工具。原生 input 支持图片 URL／file ID、此前的 `image_generation_call` 上下文，也可用 `previous_response_id` 延续多轮状态。脚本将本地 `{type: "input_image", path: ...}` 转为 data URL，并默认使用 `tool_choice: {type: "image_generation"}`。该工具的蒙版字段为 `input_image_mask`，**没有 markup 字段**。

选择参数前阅读 [API 参考、2.6 更新及旧模型能力矩阵](references/api.md)：`xhigh`／`max` 在此仅记录为 2.5 的已核实能力；markup 支持 2.5/2.6。1.5 使用固定尺寸，2／2.5 支持满足限制的自定义尺寸；GPT Image 2 的透明背景为 preview。`input_fidelity` 在 1.5 可调，2／2.5／2.6 不传。陌生模型即使在列表中，也须先核实端点和 schema，不能以实际付费请求试错。

Responses 的 `input_image_mask` 也支持本地 `{path: ...}` 引用。使用蒙版／markup 前，须先检查真实透明像素及源图与覆盖层校正方向后的尺寸。脚本检查文件签名和 PNG 头部／alpha 标记／尺寸，并解码本地 markup 检查透明像素；不检查远程图像像素或 EXIF 方向。Images 蒙版请求会本地拒绝非 PNG 的本地／data URL 源图，须先准备同格式同尺寸的 PNG 源图与蒙版。

需要复用参考图，或图像／蒙版超过 JSON data URL 上限时：

```bash
python3 scripts/imagegen.py upload --file /absolute/path/source.png --output-dir /absolute/path/uploads --dry-run
python3 scripts/imagegen.py upload --file /absolute/path/source.png --output-dir /absolute/path/uploads
```

`upload` 接受小于 50 MiB 的 PNG／JPEG／WebP，支持 `--timeout`，通过 multipart `/files` 以 `purpose=vision` 上传，将返回的 File 对象保存到 `file.json`。将其 `id` 作为原生 `file_id` 使用；该操作不生图，也不发现模型。guide 的源图／蒙版 <50 MB 要求与 JSON `image_url` 最多 20,971,520 字符是独立限制，准备大输入前须查看参考文档。

同步编辑新增 `--transport auto|json|multipart`，默认 `auto`：全部为本地路径／data URL 时使用 multipart；包含 HTTPS／file ID 时保留 JSON。单图上传字段为 `image`，多图为 `image[]`；网关要求重复 `image` 字段时可加 `--multipart-image-field image`。显式 multipart 遇到远程引用会在提交前报错。Dry-run 会显示所选传输方式；请求失败后不会自动换格式重试。`request.json` 保留规范化请求，`request-meta.json` 记录实际传输格式。

## 产物与恢复

每次在线请求保留请求 JSON、响应元数据、最终 `response.json`、图像和含绝对路径的 manifest。流式请求另保存 `events.jsonl` 与 `partial-...` 预览；完成后保存最终响应供恢复。预览不能当作最终产物。Agent 须查看实际图像，确认外观、透明度、文字及修改要求。

从已有原生 Images 或 Responses 响应恢复保存，无需再次生图：

```bash
python3 scripts/imagegen.py save --response /absolute/path/run/response.json --output-dir /absolute/path/recovered
```

保留同目录响应元数据以延续追踪。不自动重试、切换供应商／模型，也不自动为缺失图像补发请求。响应不完整、流中断／失败、超时均须先排查，请求可能已经产生费用。兼容 URL 产物下载不发送 API key，也不跟随重定向。

## Batch

官方 Batch 文档明确支持 GPT Image 2.5 的图像生成／编辑端点，不应推广到旧模型。Responses Batch 还需文档明确支持 Batch 的主模型和兼容图片工具。每份 JSONL 使用单一模型、单一端点，逐行提供唯一 `custom_id` 和标准 `method`／`url`／`body` 字段；最多 50,000 条、200 MB。本地图像／蒙版／markup 路径相对 JSONL 目录解析并在上传前转换，原始与展开后的 JSONL 均须满足上限；不启用流式。

```bash
python3 scripts/imagegen.py batch-submit --jsonl requests.jsonl --output-dir /absolute/path/batches --endpoint /images/generations --dry-run
python3 scripts/imagegen.py batch-submit --jsonl requests.jsonl --output-dir /absolute/path/batches --endpoint /images/generations
python3 scripts/imagegen.py batch-status --id batch_returned_id
python3 scripts/imagegen.py batch-download --id batch_returned_id --output-dir /absolute/path/batch-results
```

`--endpoint` 可省略，可选值为 `/images/generations`、`/images/edits`、`/responses`。提交前发现所有模型，再通过 multipart 以 `purpose=batch` 上传准备好的 JSONL，随后以 `24h` 完成窗口创建批次。下载保留原始 `output.jsonl`／`error.jsonl`，按 `custom_id` 关联保存图像，不能假设输出顺序与输入一致。仅在用户明确要求取消时使用 `batch-cancel --id ...`。不承诺特定批量折扣或所有兼容供应商均支持 Batch。

GPT Image 2.6 来源核实日期：**2026-11-05**；旧模型参考基线：**2026-11-04**。完整请求示例、蒙版文件大小与 URL 字符上限的区别、来源链接见 [references/api.md](references/api.md)。
