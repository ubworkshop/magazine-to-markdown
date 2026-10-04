# magazine-to-markdown

> Turn English magazines (EPUB & PDF) into standalone Markdown articles with extracted images and structured indexes.

An Agent Skill for extracting English magazines (e.g., *The Economist*, *The New Yorker*, *Time*, *Wired*, *Bloomberg*) into individual Markdown documents. Each article is cleanly split, formatted, and named following the `Index_Article_Title.md` convention.

## ✨ Features

- **Multi-format Support**: Seamlessly processes both `.epub` and `.pdf` magazines.
- **Smart Article Splitting**:
  - **EPUB**: Parses Spine and Nav/NCX document trees to extract individual columns, editorials, and feature stories.
  - **PDF**: Uses built-in bookmarks/TOC or automated headline (H1) font-scale analysis to detect article boundaries.
- **Images & Visual Assets**: Automatically extracts high-resolution cover art, charts, infographics, and photos into `assets/`, while rewriting relative markdown image references (`![](./assets/xxx.png)`).
- **Standardized Naming**: Outputs clean, file-system-safe filenames: `01_The_World_This_Week.md`, `02_Leaders_AI_and_the_Future.md`.
- **Auto-generated Catalog**: Builds a top-level `README.md` containing magazine metadata and one-click navigational links.

## 🚀 Installation & Setup

### 1. Requirements

- Python 3.10+
- Dependencies: `pip install pymupdf ebooklib beautifulsoup4 markdownify`

### 2. Manual CLI Usage

```bash
# Basic extraction (creates a folder named after the magazine in the current directory)
python3 scripts/extract_magazine.py "/path/to/magazine.epub"

# Process a PDF magazine
python3 scripts/extract_magazine.py "/path/to/magazine.pdf"

# Specify a custom output directory
python3 scripts/extract_magazine.py "/path/to/magazine.epub" -o "./my_magazine_notes"

# Skip image extraction (text only)
python3 scripts/extract_magazine.py "/path/to/magazine.pdf" --no-images
```

### 3. Agent Skill Integration

Place this repository into your agent's skill directory:

```bash
# For Antigravity / Claude Code
git clone https://github.com/ubworkshop/magazine-to-markdown.git ~/.gemini/config/skills/magazine-to-markdown
```

Then trigger via natural language:
- *"Extract all articles from this magazine: `The_Economist.epub`"*
- *"Convert this PDF magazine into markdown articles"*

## 📂 Output Structure

```text
The_Economist_2026/
├── README.md               # Magazine overview and clickable article index
├── assets/                 # Extracted images, charts, and cover
│   ├── cover.jpg
│   └── img_art01_p3_1.jpeg
├── 01_The_World_This_Week.md
├── 02_Leaders_AI_and_Global_Economy.md
├── 03_Briefing_The_Next_Tech_Wave.md
└── ...
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
