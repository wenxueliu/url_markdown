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

## Workflow: Content Quality Assurance

### Step 1: Initial Extraction
Run the extraction tool with default settings:
```bash
python crawlee_url.py https://example.com/article
```

### Step 2: Quality Check
**Always inspect the extracted content** for quality issues:

**❌ Warning Signs of Poor Extraction:**
- Content length > 10,000 characters (likely includes entire page)
- Contains JavaScript code: `function()`, `const `, `let `, `window.`, `document.`
- Contains CSS styles: `{`, `}`, `@media`, `transition:`, `animation:`
- Contains navigation menus: "首页", "产品服务", "关于我们", "联系我们"
- Contains footer/sidebar elements: "版权所有", "友情链接", "热门标签"
- Contains page structure: `<html>`, `<body>`, `<head>` tags

**✅ Signs of Good Extraction:**
- Content length between 1,000-8,000 characters (typical article length)
- Contains article title, author, publication date
- Contains structured content with headings (###, ####)
- Contains paragraphs, lists, images relevant to the article
- No code blocks unless the article is technical content

### Step 3: Diagnose and Configure

If quality check fails, identify the main content area:

**Option A: Use Browser DevTools**
1. Open the URL in Chrome/Firefox
2. Press F12 to open Developer Tools
3. Click the element picker (Ctrl+Shift+C)
4. Click on the article content area
5. Copy the CSS selector (right-click → Copy → Copy selector)

**Option B: Use Playwright (Built-in)**
```bash
# Navigate to the page with Playwright to inspect structure
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://example.com/article')
    page.pause()  # Inspect the page manually
    browser.close()
"
```

**Option C: Test Common Selectors**
Try these common article content selectors:
- `.article-content`, `.post-content`, `.entry-content`
- `.detail-content`, `.article-body`, `.content-body`
- `article`, `main article`, `.main-content`
- `#content`, `#article`, `#main-content`

### Step 4: Add Configuration to `url_selector_config_default.json`

Add a new configuration entry:
```json
{
  "url_pattern": "https://www.example.com/*",
  "selectors": [".article-content", ".detail-content"],
  "name": "Example Site",
  "description": "Example site article content extraction",
  "combine_strategy": "best"
}
```

**Configuration Fields:**
- `url_pattern`: URL pattern to match (supports wildcards)
- `selectors`: Array of CSS selectors to try (in order)
- `name`: Human-readable site name
- `description`: Notes about this configuration
- `combine_strategy`: How to combine multiple selectors
  - `best`: Use the longest matching content
  - `concat`: Concatenate all matches
  - `separate`: Keep matches separate

### Step 5: Verify and Iterate

Re-run the extraction:
```bash
python crawlee_url.py https://example.com/article
```

Compare the new output:
- Check content length reduction (should be 80-95% smaller)
- Verify no JavaScript/CSS in output
- Ensure article structure is preserved
- Confirm all important content is included

### Step 6: Document the Pattern

After successful configuration, add it to the knowledge base:
```markdown
## Site: Example Site
- **URL Pattern**: `https://www.example.com/*`
- **Content Selector**: `.article-content`
- **Character Reduction**: 25,570 → 2,495 (90.3% reduction)
- **Notes**: Avoids navigation, footer, sidebar elements
```

## Handling Redundant JS/CSS Content

If the extracted Markdown contains redundant JavaScript code, CSS styles, or other non-content elements, **DO NOT manually edit the output**. Instead, fix the root cause by updating `url_selector_config_default.json`.

### Common Issues and Solutions

**Issue**: Content includes entire HTML page
- **Cause**: No specific selector matched, using full page
- **Fix**: Add specific content selector for the site

**Issue**: Content includes navigation menus
- **Cause**: Selector too broad, includes parent containers
- **Fix**: Use more specific child selector

**Issue**: Content includes sidebars/related articles
- **Cause**: Selector includes sibling elements
- **Fix**: Use direct child selector or exclude selectors

### Solution: Configure CSS Selectors

**Target specific content area**:
```json
{
  "url_pattern": "https://www.example.com/news/*",
  "selectors": [".detail-content"],
  "name": "Example News",
  "description": "News article content extraction",
  "combine_strategy": "best"
}
```

## Limitations

1. **Single URL extraction**: Current implementation extracts one URL at a time. For batch processing, call the function multiple times.
2. **JavaScript-heavy sites**: Some extremely dynamic sites may require custom wait strategies
3. **Anti-bot protections**: The extractor includes anti-detection measures, but some sites may still block automated access
4. **WeChat articles**: May include inline JavaScript/CSS in the output. Consider adding exclude selectors for cleaner extraction.

## Configuration Examples

### Example 1: 53AI Knowledge Base
**Problem**: Extraction returned 25,570 characters including full page HTML, CSS, JavaScript
**Solution**: Added configuration to target `.detail-content` selector
**Result**: Reduced to 2,495 characters (90.3% reduction)

```json
{
  "url_pattern": "https://www.53ai.com/news/*",
  "selectors": [".detail-content"],
  "name": "53AI知识库",
  "description": "53AI知识库文章正文内容提取(仅提取.detail-content,避免导航、JS/CSS干扰)",
  "combine_strategy": "best"
}
```

### Example 2: WeChat Articles
**Problem**: WeChat articles include inline JavaScript and CSS styles
**Solution**: Use specific content selectors to avoid script/style tags

```json
{
  "url_pattern": "https://mp.weixin.qq.com/*",
  "selectors": ["#activity-name > span", "#js_content"],
  "name": "微信公众号",
  "description": "微信公众号文章正文内容提取(仅提取#js_content,避免JS/CSS干扰)",
  "combine_strategy": "concat"
}
```

### Example 3: CSDN Blog
**Problem**: CSDN pages include extensive navigation, ads, and sidebar
**Solution**: Target specific article containers

```json
{
  "url_pattern": "https://blog.csdn.net/*/article/details/*",
  "selectors": ["#article-header-box", "#content_views"],
  "name": "csdn博客",
  "description": "CSDN博客文章内容提取",
  "combine_strategy": "concat"
}
```

### Example 4: Zhihu Column
**Problem**: Zhihu includes complex navigation and recommendation sections
**Solution**: Extract main content area only

```json
{
  "url_pattern": "https://zhuanlan.zhihu.com/p/*",
  "selectors": ["#root > div > main > div > div.Post-Row-Content > div.Post-Row-Content-left"],
  "name": "知乎专栏",
  "description": "知乎专栏文章内容提取",
  "combine_strategy": "concat"
}
```

## Recent Updates

- **2026-02-15**: Added content quality assurance workflow with automatic configuration guidance
- **2026-02-15**: Enhanced quality check indicators to identify JS/CSS contamination
- **2026-02-15**: Successfully tested WeChat article extraction
- **2026-02-15**: Browser reuse support for faster multiple extractions
- **2026-02-15**: Improved handling of 53AI knowledge base articles
