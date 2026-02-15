---
name: crawlee-url-extractor
description: Extract and convert web page content to Markdown using Crawlee/Playwright. Use when needing to scrape web pages, extract structured content from URLs, convert HTML to Markdown, or save web content with metadata. Supports custom CSS selectors for targeted extraction, multiple content combination strategies, and automatic metadata extraction. Optimized for Chinese websites with configurable headless/headed browser modes.
---

# Crawlee URL Extractor

Extract and convert web page content to Markdown format with automatic metadata extraction.

## Overview

This skill provides a robust web scraping solution using Crawlee and Playwright, specifically optimized for websites. It automatically extracts page content, converts HTML to Markdown, and saves both the Markdown and structured JSON metadata and save tokens.

### Key Features

- **Automatic Content Extraction**: Intelligently extracts main content using CSS selectors
- **HTML to Markdown Conversion**: Clean Markdown output with proper formatting
- **Metadata Extraction**: Automatically extracts page metadata (title, author, date, etc.)
- **Chinese Website Optimization**: Pre-configured for Chinese sites (zh-CN, Asia/Shanghai timezone)
- **Flexible Browser Modes**: Headless (default) or headed for debugging
- **Configurable Output**: Custom filename or auto-generated with timestamp

### When to Use This Skill

Use this skill when:
- User asks to scrape/extract content from a web page
- User wants to convert HTML/URL to Markdown format
- User wants to save web pages as Markdown files
- User needs to extract structured content from websites
- User asks about web scraping with Playwright/Crawlee
- User wants custom CSS selectors for targeted content extraction

## Quick Start

### Command Line Usage

python crawlee_url.py https://example.com --no-headless -c url_selector_config_default.json -o output_dir -f custom_name -t timeout

## Output Files

Each extraction creates two files:

### 1. Markdown File (.md)
- Clean Markdown converted from HTML
- Proper heading, list, and code formatting
- Optimized for Chinese content

### 2. JSON File (.json)
Structured metadata including:
```json
{
  "url": "https://example.com",
  "title": "Page Title",
  "markdown_content": "Full markdown content...",
  "timestamp": "2025-02-14 00:00:00",
  "content_type": "html",
  "status_code": 200,
  "error_message": null,
  "metadata": {
    "language": "zh-CN",
    "extraction_method": "url_specific",
    "extractor_config": "config_name"
  },
  "files": {
    "md_file": "output/example.com_path_20250214_000000.md",
    "json_file": "output/example.com_path_20250214_000000.json"
  },
  "success": true
}
```

### references/requirements.txt

Python dependencies with versions from local environment:
- crawlee==1.0.4
- playwright==1.55.0
- markdownify==1.2.2
- beautifulsoup4==4.14.2
- aiohttp==3.13.2

Install dependencies:
```bash
pip install -r references/requirements.txt
playwright install  # Install Playwright browsers
```

## Best Practices

1. **Start with default settings**: The extractor works well out-of-box for most sites
2. **Use custom configs for specific sites**: Add site-specific selectors to config for better results
3. **Adjust timeout for slow sites**: Increase `--timeout` for sites with slow loading
4. **Use headed mode for debugging**: `--no-headless` helps diagnose extraction issues
5. **Check logs**: The extractor logs detailed information about the extraction process
6. **Specify filename for predictability**: Use `-f` parameter when filename matters

## Limitations

1. **Single URL extraction**: Current implementation extracts one URL at a time. For batch processing, call the function multiple times.
2. **JavaScript-heavy sites**: Some extremely dynamic sites may require custom wait strategies
3. **Anti-bot protections**: The extractor includes anti-detection measures, but some sites may still block automated access
