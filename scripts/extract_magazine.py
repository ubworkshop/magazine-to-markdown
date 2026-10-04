#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Magazine to Markdown Extractor
将英文杂志（EPUB 或 PDF 格式）中的所有文章、配图、标题等转换为独立的 Markdown 文档。
命名格式：序号 + 文章标题.md (例如: 01_The_World_This_Week.md)
"""

import os
import sys
import re
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def sanitize_filename(name: str, max_length: int = 70) -> str:
    """清理文件名中的非法字符并规范化"""
    clean = re.sub(r'[\\/*?:"<>|#\n\r\t]', '', name)
    clean = clean.strip().replace(' ', '_')
    clean = re.sub(r'_+', '_', clean)
    if not clean:
        clean = "Untitled_Article"
    return clean[:max_length]

# ==============================================================================
# EPUB 杂志处理通道
# ==============================================================================
def process_epub_magazine(epub_file: Path, output_dir: Path, save_images: bool = True):
    import ebooklib
    from ebooklib import epub
    
    print(f"📖 正在解析 EPUB 杂志: {epub_file.name} ...")
    book = epub.read_epub(str(epub_file))
    
    # 1. 提取元数据
    titles = book.get_metadata('DC', 'title')
    mag_title = titles[0][0] if titles else epub_file.stem
    print(f"📌 杂志标题: {mag_title}")
    
    # 2. 导出所有插图
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img_map = {}
    
    if save_images:
        print("🖼️  正在提取杂志配图与封面...")
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                orig_name = Path(item.get_name()).name
                target_path = assets_dir / orig_name
                with open(target_path, "wb") as f:
                    f.write(item.get_content())
                rel_path = f"./assets/{orig_name}"
                img_map[orig_name] = rel_path
                img_map[item.get_name()] = rel_path
                img_map[f"../Images/{orig_name}"] = rel_path
                img_map[f"Images/{orig_name}"] = rel_path
        print(f"   已导出 {len(set(img_map.values()))} 张插图至 assets/")

    # 3. 按 spine 处理每篇文章
    articles = []
    article_index = 1

    for item_id, linear in book.spine:
        item = book.get_item_with_id(item_id)
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
            
        content = item.get_content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # 移除无用标签
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
            
        # 提取文章标题 (优先 h1, h2, title, 或特定的文章标题 class)
        title = ""
        for selector in ['h1', '.article-headline', '.rubric', 'h2', 'title']:
            header = soup.select_one(selector)
            if header and header.get_text().strip():
                candidate = header.get_text().strip()
                # 过滤无意义的空标题
                if len(candidate) > 2 and not candidate.lower().startswith("table of contents"):
                    title = candidate
                    break
                    
        # 替换图片路径
        for img in soup.find_all('img'):
            src = img.get('src', '')
            src_name = Path(src).name
            if src_name in img_map:
                img['src'] = img_map[src_name]
            elif src in img_map:
                img['src'] = img_map[src]

        for svg_img in soup.find_all(['image', 'svg:image']):
            href = svg_img.get('xlink:href') or svg_img.get('href')
            if href:
                href_name = Path(href).name
                if href_name in img_map:
                    new_img = soup.new_tag("img", src=img_map[href_name])
                    svg_img.replace_with(new_img)

        # 转换为 Markdown
        article_md = md(str(soup), heading_style="ATX", bullets_style="-", strip=['script', 'style']).strip()
        article_md = re.sub(r'\n{3,}', '\n\n', article_md)
        
        # 过滤掉过于短小且无图的内容（例如版权声明残页）
        if len(article_md.split()) < 20 and "![" not in article_md:
            continue
            
        if not title:
            # 从正文第一行尝试提取
            first_line = article_md.splitlines()[0] if article_md.splitlines() else ""
            clean_first = re.sub(r'^[#*_\s]+', '', first_line).strip()
            title = clean_first[:50] if clean_first else f"Article_{article_index:02d}"
            
        title = re.sub(r'\s+', ' ', title).strip()
        safe_title = sanitize_filename(title)
        filename = f"{article_index:02d}_{safe_title}.md"
        file_path = output_dir / filename
        
        # 写入独立的 Markdown 文件
        with open(file_path, "w", encoding="utf-8") as f:
            if not article_md.startswith("# "):
                f.write(f"# {title}\n\n")
            f.write(article_md)
            f.write("\n")
            
        articles.append({
            "index": article_index,
            "title": title,
            "filename": filename
        })
        article_index += 1

    generate_index(output_dir, mag_title, articles)


# ==============================================================================
# PDF 杂志处理通道
# ==============================================================================
def process_pdf_magazine(pdf_file: Path, output_dir: Path, save_images: bool = True):
    import fitz  # PyMuPDF
    
    print(f"📖 正在解析 PDF 杂志: {pdf_file.name} ...")
    doc = fitz.open(str(pdf_file))
    mag_title = doc.metadata.get("title") or pdf_file.stem
    print(f"📌 杂志标题: {mag_title}")
    print(f"📄 总页数: {len(doc)}")
    
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 尝试从 PDF 书签(TOC)切分文章
    toc = doc.get_toc() # [[lvl, title, page], ...]
    sections = []
    
    if toc:
        # 只取第一级和第二级书签作为独立文章
        filtered_toc = [item for item in toc if item[0] <= 2 and item[1].strip()]
        for i, item in enumerate(filtered_toc):
            title = item[1].strip()
            start_page = max(0, item[2] - 1)
            if i + 1 < len(filtered_toc):
                end_page = max(start_page, filtered_toc[i + 1][2] - 2)
            else:
                end_page = len(doc) - 1
            sections.append((title, start_page, end_page))
            
    # 如果 PDF 没有目录大纲，则按每 2~4 页或主标题字号切分
    if not sections:
        print("ℹ️  未检测到内置书签，启动版面大标题检测切分...")
        # 扫描每一页中字号最大的文本行作为可能的新文章起点
        current_title = "Cover_and_Introduction"
        current_start = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            max_size = 0
            page_top_header = ""
            for b in blocks:
                if b.get("type") == 0: # text
                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            txt = s.get("text", "").strip()
                            size = s.get("size", 0)
                            if size > max_size and len(txt) > 3:
                                max_size = size
                                page_top_header = txt
            # 杂志大标题通常明显大于正文字号 (>= 22pt)
            if max_size >= 24 and page_num > current_start:
                sections.append((current_title, current_start, page_num - 1))
                current_title = page_top_header
                current_start = page_num
        sections.append((current_title, current_start, len(doc) - 1))

    print(f"✂️  共切分为 {len(sections)} 篇文章...")
    
    articles = []
    article_index = 1
    
    for title, start_p, end_p in sections:
        article_text_blocks = []
        article_images = []
        
        for p in range(start_p, end_p + 1):
            page = doc[p]
            # 提取文字
            text = page.get_text("text").strip()
            if text:
                article_text_blocks.append(text)
                
            # 提取图片
            if save_images:
                img_list = page.get_images(full=True)
                for img_idx, img_info in enumerate(img_list):
                    xref = img_info[0]
                    base_img = doc.extract_image(xref)
                    img_bytes = base_img["image"]
                    img_ext = base_img["ext"]
                    img_filename = f"img_art{article_index:02d}_p{p+1}_{img_idx+1}.{img_ext}"
                    img_dest = assets_dir / img_filename
                    with open(img_dest, "wb") as f:
                        f.write(img_bytes)
                    article_images.append(f"./assets/{img_filename}")

        if not article_text_blocks and not article_images:
            continue
            
        safe_title = sanitize_filename(title)
        filename = f"{article_index:02d}_{safe_title}.md"
        file_path = output_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"> *Source: Pages {start_p + 1} - {end_p + 1}*\n\n")
            
            # 如果有提取出的首图/主图，插在文首
            if article_images:
                f.write(f"![Illustration]({article_images[0]})\n\n")
                
            # 写入正文
            for block in article_text_blocks:
                # 简单清洗段落换行
                clean_para = re.sub(r'(?<!\n)\n(?!\n)', ' ', block)
                f.write(clean_para + "\n\n")
                
            # 附加其他插图
            if len(article_images) > 1:
                f.write("\n### Figures & Illustrations\n\n")
                for other_img in article_images[1:]:
                    f.write(f"![Figure]({other_img})\n\n")
                    
        articles.append({
            "index": article_index,
            "title": title,
            "filename": filename
        })
        article_index += 1

    generate_index(output_dir, mag_title, articles)


def generate_index(output_dir: Path, title: str, articles: list):
    """生成杂志目录索引文件 README.md"""
    readme_path = output_dir / "README.md"
    print(f"📝 正在生成杂志文章清单: {readme_path.name} ...")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"本杂志包含 **{len(articles)}** 篇独立文章与专栏。点击下方链接可直达阅读对应文章：\n\n")
        f.write("---\n\n## 📑 文章目录\n\n")
        for art in articles:
            f.write(f"- [{art['index']:02d}. {art['title']}](./{art['filename']})\n")
            
    print(f"\n🎉 提取完成！")
    print(f"📂 输出目录: {output_dir}")
    print(f"📚 文章总数: {len(articles)}")
    print(f"📑 目录索引: {readme_path}")


def main():
    parser = argparse.ArgumentParser(description="将英文杂志(EPUB/PDF)转换为独立的 Markdown 文章与配图")
    parser.add_argument("input", help="杂志文件路径 (.epub 或 .pdf)")
    parser.add_argument("-o", "--output", help="输出目录 (默认为当前目录/杂志名)", default=None)
    parser.add_argument("--no-images", action="store_true", help="跳过图片提取")
    
    args = parser.parse_args()
    input_path = Path(args.input).resolve()
    
    if not input_path.exists():
        print(f"错误: 文件不存在 -> {input_path}", file=sys.stderr)
        sys.exit(1)
        
    ext = input_path.suffix.lower()
    if ext not in ['.epub', '.pdf']:
        print(f"错误: 仅支持 .epub 或 .pdf 格式杂志 (当前输入: {ext})", file=sys.stderr)
        sys.exit(1)
        
    if not args.output:
        out_dir = Path.cwd() / input_path.stem
    else:
        out_dir = Path(args.output).resolve()
        
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if ext == '.epub':
        process_epub_magazine(input_path, out_dir, save_images=not args.no_images)
    else:
        process_pdf_magazine(input_path, out_dir, save_images=not args.no_images)

if __name__ == "__main__":
    main()
