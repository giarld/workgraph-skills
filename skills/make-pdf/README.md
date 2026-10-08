# Make PDF

[简体中文](README.zh-CN.md)

Turn outlines, notes, transcripts, articles, screenshots, diagrams, datasets, or mixed research materials into a complete LaTeX document and a compiled PDF. Suitable for technical reports, lecture notes, tutorials, reading notes, and illustrated explainers.

## Prerequisites

- A TeX distribution such as TeX Live or MiKTeX with `xelatex` available on `PATH`. `latexmk` is preferred; repeated `xelatex` runs are the fallback.
- The template requires `fontspec` or `ctex`, plus `amsmath`, `amssymb`, `graphicx`, `geometry`, `listings`, and `hyperref`. Chinese documents should use `ctex` with the Fandol fonts and CJK support.
- Optional packages include `tcolorbox`, `booktabs`, `subcaption`, `float`, `tikz`, and `pgfplots`. The template uses fallbacks for missing `ctex` and `tcolorbox`; features that need other optional packages require those packages to be installed.
- Source materials and any referenced images must be accessible to the agent.

## Usage

Invoke the skill with your materials, intended audience, language, and output location, for example:

```text
Use $make-pdf to turn notes.md and the figures/ directory into an English
technical report. Include a title page, table of contents, and figure captions.
Save the LaTeX source, referenced figures, and compiled PDF under output/report/.
```

The agent inspects the materials, designs the document structure, fills `assets/document-template.tex`, writes the content, compiles it, and checks the compilation log. Detailed workflow instructions live in [SKILL.md](SKILL.md).

For an existing generated document, the preferred compilation command is:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error report.tex
```

If `latexmk` is unavailable, run `xelatex -interaction=nonstopmode -halt-on-error report.tex` enough times to resolve references and the table of contents.

## Configuration

No API keys or skill-specific environment variables are required. `config.json` declares version 1 with an empty `environment` array. Install the TeX toolchain separately; the configuration file does not install dependencies.

## Outputs and limitations

Deliver the completed `.tex` source, all referenced figure assets, and the compiled PDF. Useful generated charts or logs may also be included. The bundled template is a starting point: its metadata and body placeholders must be filled before final delivery.

Adding this package does not prove that the host can compile documents. Missing TeX packages, fonts, or source assets must be resolved during actual use. The plain XeLaTeX fallback does not guarantee Chinese rendering without CJK support.

## Source

Converted from [giarld/skills: make-pdf](https://github.com/giarld/skills/tree/6d579a96ee3d4376295428aa16cb83a49eae514f/make-pdf), commit `6d579a96ee3d4376295428aa16cb83a49eae514f`. The upstream `SKILL.md` and LaTeX template are preserved unchanged; generated `.aux`, `.log`, `.out`, `.toc`, and sample PDF artifacts are excluded. English and Simplified Chinese documentation and the OpenWorkgraph configuration declaration are added here.

No license file was present in the upstream repository root or this skill directory at that revision; this attribution does not assert an upstream license.
