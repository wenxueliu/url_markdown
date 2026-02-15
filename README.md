# Crawlee URL Extractor

[English](#english) | [中文](#中文)

---

## English

Extract and convert web page content to Markdown format with automatic metadata extraction.

### Overview

This is a robust web scraping solution using Crawlee and Playwright, specifically optimized for Chinese websites. It automatically extracts page content, converts HTML to Markdown, and saves both the Markdown and structured JSON metadata.

### Key Features

- **Automatic Content Extraction**: Intelligently extracts main content using CSS selectors
- **HTML to Markdown Conversion**: Clean Markdown output with proper formatting
- **Metadata Extraction**: Automatically extracts page metadata (title, author, date, etc.)
- **Chinese Website Optimization**: Pre-configured for Chinese sites (zh-CN, Asia/Shanghai timezone)
- **Flexible Browser Modes**: Headless (default) or headed for debugging
- **Configurable Output**: Custom filename or auto-generated with timestamp

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Quick Start

#### Command Line Usage

```bash
python crawlee_url.py https://example.com --no-headless -c url_selector_config_default.json -o output_dir -f custom_name -t timeout
```

#### Parameters

- `url`: Target URL to scrape (required)
- `--no-headless`: Run browser in headed mode (useful for debugging)
- `-c, --config`: Path to selector config file (default: `url_selector_config_default.json`)
- `-o, --output`: Output directory (default: `output/`)
- `-f, --filename`: Custom filename for output files
- `-t, --timeout`: Page load timeout in seconds (default: 30)

If content contains JS or CSS rendering issues, fix by modifying `url_selector_config_default.json`

### Output Files

Each extraction creates two files:

#### 1. Markdown File (.md)
- Clean Markdown converted from HTML
- Proper heading, list, and code formatting
- Optimized for Chinese content

#### 2. JSON File (.json)
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

### Best Practices

1. **Start with default settings**: The extractor works well out-of-box for most sites
2. **Use custom configs for specific sites**: Add site-specific selectors to config for better results
3. **Adjust timeout for slow sites**: Increase `--timeout` for sites with slow loading
4. **Use headed mode for debugging**: `--no-headless` helps diagnose extraction issues
5. **Check logs**: The extractor logs detailed information about the extraction process
6. **Specify filename for predictability**: Use `-f` parameter when filename matters

### Limitations

1. **Single URL extraction**: Current implementation extracts one URL at a time. For batch processing, call the function multiple times
2. **JavaScript-heavy sites**: Some extremely dynamic sites may require custom wait strategies
3. **Anti-bot protections**: The extractor includes anti-detection measures, but some sites may still block automated access

---

## 中文

# Crawlee URL 提取器

使用 Crawlee/Playwright 将网页内容提取并转换为 Markdown 格式，自动提取元数据。

### 概述

这是一个基于 Crawlee 和 Playwright 的强大网页抓取解决方案，专门针对中文网站优化。它可以自动提取页面内容，将 HTML 转换为 Markdown，并保存 Markdown 文件和结构化的 JSON 元数据。

### 核心特性

- **自动内容提取**：使用 CSS 选择器智能提取主要内容
- **HTML 转 Markdown**：输出格式规范的 Markdown
- **元数据提取**：自动提取页面元数据（标题、作者、日期等）
- **中文网站优化**：预配置中文网站设置（zh-CN，亚洲/上海时区）
- **灵活的浏览器模式**：支持无头模式（默认）或有头模式（用于调试）
- **可配置的输出**：自定义文件名或使用时间戳自动生成

### 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install
```

### 快速开始

#### 命令行使用

```bash
python crawlee_url.py https://example.com --no-headless -c url_selector_config_default.json -o output_dir -f custom_name -t timeout
```

#### 参数说明

- `url`：目标网址（必需）
- `--no-headless`：使用有头浏览器模式（便于调试）
- `-c, --config`：选择器配置文件路径（默认：`url_selector_config_default.json`）
- `-o, --output`：输出目录（默认：`output/`）
- `-f, --filename`：输出文件的自定义文件名
- `-t, --timeout`：页面加载超时时间（秒，默认：30）

如果内容包含 JS 或 CSS 渲染问题，可通过修改 `url_selector_config_default.json` 修复

### 输出文件

每次提取会生成两个文件：

#### 1. Markdown 文件 (.md)
- 从 HTML 转换的干净 Markdown
- 规范的标题、列表和代码格式
- 针对中文内容优化

#### 2. JSON 文件 (.json)
结构化元数据，包括：
```json
{
  "url": "https://example.com",
  "title": "页面标题",
  "markdown_content": "完整的 markdown 内容...",
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

### 最佳实践

1. **从默认设置开始**：提取器对大多数网站开箱即用
2. **为特定网站使用自定义配置**：在配置中添加网站特定的选择器以获得更好的效果
3. **为慢速网站调整超时**：对于加载缓慢的网站，增加 `--timeout` 参数
4. **使用有头模式进行调试**：`--no-headless` 有助于诊断提取问题
5. **检查日志**：提取器会记录关于提取过程的详细信息
6. **指定文件名以提高可预测性**：当文件名很重要时，使用 `-f` 参数

### 限制

1. **单 URL 提取**：当前实现一次只能提取一个 URL。如需批量处理，请多次调用函数
2. **重度 JavaScript 网站**：一些高度动态的网站可能需要自定义等待策略
3. **反爬虫保护**：提取器包含反检测措施，但某些网站仍可能阻止自动化访问

---

## 创建为 Claude Skill

要将此项目创建为 Claude Skill，只需在 Claude Code 中使用 `/skill-creator` 命令即可。skill-creator 会自动引导你完成整个流程。

### 快速步骤

1. 在 Claude Code 中运行：`/skill-creator`
2. 按照提示完成：
   - 配置 skill 元数据（名称、描述）
   - 组织项目文件到正确的 skill 结构
   - 生成 SKILL.md
   - 打包为 `.skill` 文件

skill-creator 会自动处理所有技术细节。

---

## Creating as Claude Skill

To create this project as a Claude Skill, simply use the `/skill-creator` command in Claude Code. The skill-creator will guide you through the entire process automatically.

### Quick Steps

1. In Claude Code, run: `/skill-creator`
2. Follow the guided prompts to:
   - Configure skill metadata (name, description)
   - Organize project files into proper skill structure
   - Generate SKILL.md
   - Package as `.skill` file

The skill-creator handles all the technical details automatically.

---

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
