# Make PDF

[English](README.md)

将提纲、笔记、转录稿、文章、截图、图表、数据集或混合研究材料整理为完整的 LaTeX 文档，并编译成 PDF。适用于技术报告、讲义、教程、阅读笔记和带图解的说明文档。

## 前置条件

- 安装 TeX Live 或 MiKTeX 等 TeX 发行版，并确保 `xelatex` 可通过 `PATH` 调用。推荐使用 `latexmk`，缺少时可重复运行 `xelatex`。
- 模板需要 `fontspec` 或 `ctex`，以及 `amsmath`、`amssymb`、`graphicx`、`geometry`、`listings` 和 `hyperref`。中文文档建议使用 `ctex`、Fandol 字体和 CJK 支持。
- 可选宏包包括 `tcolorbox`、`booktabs`、`subcaption`、`float`、`tikz` 和 `pgfplots`。模板在缺少 `ctex` 和 `tcolorbox` 时提供降级方式；使用其他可选宏包对应的功能时，仍需安装相关宏包。
- Agent 必须能够访问源材料和文档引用的图片。

## 使用方式

调用时提供材料、目标读者、语言和输出位置，例如：

```text
使用 $make-pdf 将 notes.md 和 figures/ 目录整理为中文技术报告。
包含标题页、目录和图注，将 LaTeX 源文件、引用图片和编译后的 PDF
保存到 output/report/。
```

Agent 会检查材料、设计文档结构、填充 `assets/document-template.tex`、撰写正文、编译并检查日志。详细工作流程见 [SKILL.md](SKILL.md)。

对于已经生成的文档，推荐使用以下编译命令：

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error report.tex
```

如果没有 `latexmk`，重复执行 `xelatex -interaction=nonstopmode -halt-on-error report.tex`，直到交叉引用和目录得到解析。

## 配置

无需 API 密钥或技能专用环境变量。`config.json` 使用版本 1，`environment` 数组为空。TeX 工具链需要单独安装，配置文件不会安装依赖。

## 输出与限制

交付完整的 `.tex` 源文件、全部引用图片和编译后的 PDF。必要时可附带有用的生成图表或日志。内置模板是文档起点，最终交付前必须填写元数据和正文占位内容。

加入技能包并不代表宿主环境已经能够编译文档。实际使用时，需要解决缺失的 TeX 宏包、字体或源素材。没有 CJK 支持时，普通 XeLaTeX 降级方式不保证中文正常显示。

## 来源

转换自 [giarld/skills 的 make-pdf](https://github.com/giarld/skills/tree/6d579a96ee3d4376295428aa16cb83a49eae514f/make-pdf)，源提交为 `6d579a96ee3d4376295428aa16cb83a49eae514f`。原样保留上游 `SKILL.md` 和 LaTeX 模板，不包含生成的 `.aux`、`.log`、`.out`、`.toc` 和示例 PDF 文件。本仓库补充英文、简体中文文档及 OpenWorkgraph 配置声明。

该版本的上游仓库根目录和技能目录中均未提供许可证文件；来源记录不代表对上游许可作出声明。
