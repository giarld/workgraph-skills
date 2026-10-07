# VideoGen H3

通过 MiniMax H3 V2 API 生成和下载视频。支持文生视频、首帧／尾帧图生视频、图片／视频／音频多模态参考，以及将符合要求的 H3 768P 生成视频再生成为 2K。

## 前置条件与配置

- Python 3.8 或更高版本；脚本仅依赖标准库。
- 在线操作需要 API 访问权限及足够额度。自定义端点必须兼容 MiniMax V2 schema。
- 使用媒体输入时，提供可访问的媒体 URL、平台文件引用或 data URI。本地路径不能直接作为 URL 提交。

| 环境变量 | 是否必需 | 用途 |
| --- | --- | --- |
| `VIDEOGEN_H3_API_KEY` | 在线操作必需 | Bearer API 密钥；本地 dry-run 无需密钥。 |
| `VIDEOGEN_H3_API_BASE_URL` | 否 | 完整 V2 基础地址，默认 `https://api.minimax.cn/v2`；空值或无效覆盖值会报错。 |

在运行 Agent 的环境中配置密钥，不要粘贴到提示词或请求文件。[config.json](config.json) 仅声明配置输入，不设置环境变量，也不存储密钥值。尚未验证 OpenWorkgraph 应用端的配置解析和环境注入。

## 使用方式

Agent 请求示例：

- “使用 $videogen-h3 生成一段五秒的海边日出视频。”
- “使用 $videogen-h3 将这些首帧和尾帧图片生成视频。”
- “使用 $videogen-h3 结合这张人物图、运镜视频和声音参考生成视频。”
- “使用 $videogen-h3 将符合要求的任务 TASK_ID 再生成为 2K。”
- “使用 $videogen-h3 查询 TASK_ID 并下载已完成的视频。”

默认使用 `MiniMax-H3`、`768P`、5 秒，文生视频比例为 `16:9`。Agent 会显式填写请求参数；脚本不会补齐缺失的默认值。如需极速版，请明确指定 `MiniMax-H3-Max`。

手动使用时，按 [API 参考](references/api.md) 准备 JSON，然后在本技能目录运行：

```bash
python3 scripts/h3.py create --json request.json --dry-run
python3 scripts/h3.py create --json request.json
python3 scripts/h3.py regenerate --json regen.json
python3 scripts/h3.py query --task-id TASK_ID
python3 scripts/h3.py wait --task-id TASK_ID --timeout 900 --interval 15
python3 scripts/h3.py download --task-id TASK_ID --output /absolute/path/video.mp4
```

`regenerate` 也支持 `--dry-run`，可在没有密钥、不联网的情况下做本地校验。Agent 执行流程见英文 [SKILL.md](SKILL.md)。

## 产物与限制

提交后返回任务 ID；查询返回状态，成功时返回临时视频 URL。下载后返回绝对路径，不覆盖已有文件。保留任务 ID 和原始请求文件，以便恢复。Agent 会交付本地视频预览及实际输出规格。

- 查询范围为最近 7 天；成功后应及时下载，避免 URL 过期。
- 再生成仅适用于符合 H3 768P 规格的生成视频。任务 ID 模式需要白名单；源视频模式必须保留最终提示词和全部原始参考媒体。
- 脚本校验 JSON 结构及请求大小，不探测远端媒体属性，也不覆盖所有服务端限制。
- 创建／再生成不会自动重试。提交结果不确定时，先排查再决定是否新建付费任务。等待超时后可继续查询同一任务。
- 查询／等待遇到失败或取消任务时退出码为 `1`；等待超时为 `2`；成功命令为 `0`。

API 规格沿用源技能的核对日期 2026-10-06。包校验不代表已通过在线 API 实测或应用端集成验证。

[English](README.md)
