---
name: magazine-to-markdown
description: 将英文杂志（支持 EPUB 和 PDF 格式，如 The Economist、The New Yorker、Time、Wired、Bloomberg 等）按照文章篇目精准拆分为独立的 Markdown 文档，同时提取杂志中的高清配图、图表和封面，并在 Markdown 中重定向图片相对路径。文件命名严格遵循"序号+文章标题.md"，并自动生成 README.md 杂志目录索引。触发场景：用户提到"转英文杂志"、"杂志切分文章"、"提取杂志"、"杂志转markdown"、"拆解杂志"等。
---

# 英文杂志转 Markdown 独立文章 (magazine-to-markdown)

将整本英文杂志（`.epub` 或 `.pdf`）自动拆解为一套包含独立文章、精美配图与全刊索引的 Markdown 文件夹。

## 核心能力

1. **智能文章切分**：
   - **EPUB 杂志**：自动解析 Spine 与 Nav/NCX 目录树，将每一个独立专栏、社论或深度报道切分为单个 `.md`。
   - **PDF 杂志**：自动提取原生内置书签（Bookmarks/TOC）；若无书签，则启动版面大标题（H1）字号突变检测算法，按文章边界智能分篇。
2. **规范文件命名**：严格遵循用户指定的 **`序号_文章标题.md`** 格式（例如 `01_The_World_This_Week.md`、`02_Leaders_AI_and_Global_Economy.md`）。
3. **高清插图与封面提取**：全书所有配图、信息图表抽取到 `assets/` 文件夹中，Markdown 正文内自动重写为相对路径引用（`![](./assets/xxx.png)`）。
4. **全刊导航目录**：自动生成 `README.md`，列出杂志名称、文章总数及所有文章的快速跳转链接，方便直接在 Obsidian、Notion 或本地 Markdown 查看器中浏览。

## 执行命令

使用本机的专用 Python 虚拟环境执行核心转换脚本：

```bash
~/.agent-reach-venv/bin/python3 ~/.gemini/config/skills/magazine-to-markdown/scripts/extract_magazine.py "<MAGAZINE_PATH>" -o "<OUTPUT_DIR>"
```

### 参数说明：
- `<MAGAZINE_PATH>`：杂志文件的绝对或相对路径（支持 `.epub` 或 `.pdf`）。
- `-o, --output`：保存的输出目录。如不指定，默认在当前目录下生成以杂志名命名的文件夹。
- `--no-images`：可选参数，跳过提取插图。

## 典型输出目录结构

```text
The_Economist_2026/
├── README.md               # 杂志总览与完整文章索引（带跳转链接）
├── assets/                 # 提取出的全部配图、图表与封面
│   ├── cover.jpg
│   └── img_art01_p3_1.jpeg
├── 01_The_World_This_Week.md
├── 02_Leaders_Navigating_the_Storm.md
├── 03_Briefing_The_Next_Tech_Wave.md
└── ...
```

## Agent 执行流程

当用户要求提取或转换英文杂志时：
1. 确认用户提供的英文杂志文件路径（若用户只给出文件名，在当前工作区中搜寻匹配）。
2. 执行提取命令：
   `~/.agent-reach-venv/bin/python3 ~/.gemini/config/skills/magazine-to-markdown/scripts/extract_magazine.py "<MAGAZINE_PATH>" -o "<OUTPUT_DIR>"`
3. 执行完成后，查看生成的 `README.md`，向用户汇报文章切分总数、配图数量及输出目录路径。
