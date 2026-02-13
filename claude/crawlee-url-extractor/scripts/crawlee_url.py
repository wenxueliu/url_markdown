#!/usr/bin/env python
# encoding: utf-8

import asyncio
import logging
import json
import os
import re
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, unquote

from crawlee._log_config import configure_logger
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from markdownify import markdownify as md
from bs4 import BeautifulSoup

# 配置日志
main_logger = logging.getLogger('__main__')
main_logger.propagate = False
logger = logging.getLogger(__name__)
configure_logger(logger, remove_old_handlers=True)
logger.propagate = False

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

# 文件处理器
file_handler = RotatingFileHandler(
    'crawlee_url.log',
    maxBytes=1024*1024,  # 1MB
    backupCount=5,       # 保留5个备份
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 控制台处理器
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)
logger.addHandler(sh)


@dataclass
class UrlSelectorConfig:
    """URL选择器配置数据类"""
    url_pattern: str  # URL匹配模式，支持通配符
    selectors: List[str]  # 要提取的选择器列表
    name: str = ""  # 配置名称
    description: str = ""  # 配置描述
    combine_strategy: str = "concat"  # 内容组合策略：concat, separate, best

    def __post_init__(self):
        if not self.name:
            self.name = self.url_pattern


@dataclass
class UrlContent:
    """URL内容数据类"""
    url: str
    title: str = ""
    content: str = ""
    html_content: str = ""
    markdown_content: str = ""
    timestamp: str = ""
    content_type: str = ""
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.metadata is None:
            self.metadata = {}


class UrlContentExtractor:
    """URL内容提取器"""

    def __init__(self, output_dir: str = "urls",
                 window_position=(100, 100), window_size=(1280, 720),
                 wait_timeout: int = 60, headless: bool = True,
                 selector_config_file: Optional[str] = None,
                 output_filename: Optional[str] = None):
        self.output_dir = output_dir
        self.wait_timeout = wait_timeout
        self.headless = headless
        self.window_position = window_position
        self.window_size = window_size
        self.selector_config_file = selector_config_file
        self.output_filename = output_filename  # 输出文件名，None时自动生成
        self.url_selector_configs: List[UrlSelectorConfig] = []

        # 加载URL选择器配置
        self._load_selector_config()

        # 浏览器启动选项
        launch_options = {
            "headless": headless,
            "args": [
                f"--window-position={window_position[0]},{window_position[1]}",
                f"--window-size={window_size[0]},{window_size[1]}",
                "--force-device-scale-factor=1",
                "--disable-features=TranslateUI",
                "--disable-infobars",
                "--disable-extensions",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"  # 防止被检测为自动化工具
            ]
        }

        # 视口配置，特别针对中文网站优化
        browser_context_options = {
            "viewport": {"width": window_size[0], "height": window_size[1]},
            "ignore_default_args": ["--enable-blink-features=IdleDetection"],
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "locale": "zh-CN",  # 设置中文语言环境
            "timezone_id": "Asia/Shanghai"  # 设置中国时区
        }

        # 创建爬虫
        self.crawler = PlaywrightCrawler(
            browser_launch_options=launch_options,
            browser_new_context_options=browser_context_options,
            request_handler_timeout=timedelta(seconds=wait_timeout)
        )

        # 注册请求处理器
        self.crawler.router.default_handler(self.request_handler)

        # 创建输出目录
        self._ensure_output_directory()

    def _load_selector_config(self):
        """加载URL选择器配置

        加载顺序：
        1. 先从 url_selector_config_default.json 读取默认配置
        2. 如果 self.selector_config_file 不为空且文件存在，从该文件读取配置
        3. 当有相同的 url_pattern 时，用自定义配置覆盖默认配置；否则保留默认配置
        """
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_config_path = os.path.join(current_dir, 'url_selector_config_default.json')

        # 使用字典来管理配置，以 url_pattern 为键
        config_dict: Dict[str, UrlSelectorConfig] = {}

        # 第一步：加载默认配置
        try:
            if os.path.exists(default_config_path):
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                for config_item in config_data.get('url_configs', []):
                    config = UrlSelectorConfig(**config_item)
                    config_dict[config.url_pattern] = config

                logger.info(f"成功从默认配置文件加载 {len(config_dict)} 个URL选择器配置")
            else:
                logger.warning(f"默认配置文件 {default_config_path} 不存在")
        except Exception as e:
            logger.warning(f"加载默认配置文件失败: {e}，继续加载自定义配置")

        # 第二步：如果指定了自定义配置文件，合并配置
        if self.selector_config_file:
            try:
                if os.path.exists(self.selector_config_file):
                    with open(self.selector_config_file, 'r', encoding='utf-8') as f:
                        custom_config_data = json.load(f)

                    # 统计覆盖和新增的配置数量
                    override_count = 0
                    new_count = 0

                    for config_item in custom_config_data.get('url_configs', []):
                        config = UrlSelectorConfig(**config_item)
                        if config.url_pattern in config_dict:
                            # 相同的 url_pattern，覆盖默认配置
                            config_dict[config.url_pattern] = config
                            override_count += 1
                            logger.debug(f"覆盖默认配置: {config.url_pattern}")
                        else:
                            # 新增的配置
                            config_dict[config.url_pattern] = config
                            new_count += 1
                            logger.debug(f"新增配置: {config.url_pattern}")

                    logger.info(f"成功从自定义配置文件 {self.selector_config_file} 加载配置")
                    logger.info(f"  - 覆盖 {override_count} 个默认配置")
                    logger.info(f"  - 新增 {new_count} 个配置")
                    logger.info(f"  - 总计 {len(config_dict)} 个URL选择器配置")
                else:
                    logger.info(f"自定义配置文件 {self.selector_config_file} 不存在，使用默认配置")
            except Exception as e:
                logger.warning(f"加载自定义配置文件失败: {e}，使用默认配置")
                if not config_dict:
                    logger.error("默认配置和自定义配置均加载失败，URL选择器配置为空")

        # 将字典转换为列表
        self.url_selector_configs = list(config_dict.values())

    def _match_url_config(self, url: str) -> Optional[UrlSelectorConfig]:
        """根据URL匹配选择器配置"""
        parsed_url = urlparse(url)
        url_host = parsed_url.netloc
        url_path = parsed_url.path

        for config in self.url_selector_configs:
            pattern = config.url_pattern

            # 支持通配符匹配
            if '*' in pattern:
                # 将通配符转换为正则表达式
                import fnmatch
                if fnmatch.fnmatch(url, pattern) or fnmatch.fnmatch(f"{url_host}{url_path}", pattern):
                    return config
            else:
                # 精确匹配或包含匹配
                if pattern in url or url.startswith(pattern) or url.endswith(pattern):
                    return config

        return None

    def _ensure_output_directory(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建输出目录: {self.output_dir}")

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不合法字符"""
        # 移除或替换不合法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.replace(' ', '_')
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename

    def _generate_filename(self, url: str, content_type: str = "html") -> str:
        """根据URL生成文件名"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = unquote(parsed.path.strip('/'))

        if path:
            filename = f"{domain}_{path[:50]}"
        else:
            filename = domain

        filename = self._sanitize_filename(filename)

        # 添加时间戳避免重复
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 根据内容类型确定文件扩展名
        extensions = {
            "html": "html",
            "json": "json",
            "txt": "txt",
            "md": "md",
            "markdown": "md"
        }

        ext = extensions.get(content_type, "html")
        return f"{self.output_dir}/{filename}_{timestamp}.{ext}"

    async def extract_page_content(self, context: PlaywrightCrawlingContext) -> UrlContent:
        """提取页面内容"""
        url = context.request.url
        logger.info(f"正在提取页面内容: {url}")

        content = UrlContent(url=url)

        try:
            # 增强等待策略，特别针对中文网站
            # 1. 先等待DOM加载
            await context.page.wait_for_load_state('domcontentloaded',
                                                   timeout=self.wait_timeout * 1000)

            # 2. 额外等待JavaScript执行（中文网站常用）
            await asyncio.sleep(2)

            # 3. 等待网络空闲（针对动态加载内容）
            try:
                await context.page.wait_for_load_state('networkidle', timeout=self.wait_timeout *1000)
            except:
                # 如果网络空闲等待失败，继续执行
                logger.warning("网络空闲等待超时，继续执行内容提取")

            # 获取基本信息
            content.title = await context.page.title()
            content.status_code = context.response.status if context.response else None

            # 获取HTML内容
            content.html_content = await context.page.content()

            # 转换HTML为Markdown
            if content.html_content:
                content.markdown_content = self._convert_to_markdown(content.html_content)

            # 提取文本内容
            await self._extract_text_content(context, content)

            # 获取页面元数据
            await self._extract_metadata(context, content)

            # 检测内容类型
            content.content_type = self._detect_content_type(content)

            logger.info(f"成功提取页面内容: {content.title}")
            content.success = True

        except Exception as e:
            logger.error(f"提取页面内容失败: {e}")
            content.error_message = str(e)
            content.success = False

        return content

    async def _extract_text_content(self, context: PlaywrightCrawlingContext, content: UrlContent):
        """提取页面文本内容"""
        try:
            url = context.request.url

            # 检查是否有URL特定的配置
            url_config = self._match_url_config(url)

            if url_config:
                logger.info(f"使用URL特定配置: {url_config.name}")
                content.metadata['extractor_config'] = url_config.name
                extracted_content = await self._extract_with_config(context, url_config)
                content.markdown_content = self._convert_to_markdown(extracted_content)
                content.metadata['extraction_method'] = 'url_specific'

        except Exception as e:
            logger.warning(f"提取文本内容时出错: {e}")
            content.content = ""

    async def _extract_with_config(self, context: PlaywrightCrawlingContext, config: UrlSelectorConfig) -> str:
        """使用配置提取内容"""
        logger.info(f"使用配置 '{config.name}' 提取内容，选择器: {config.selectors}")

        extracted_texts = []
        selector_results = []

        for selector in config.selectors:
            try:
                elements = await context.page.query_selector_all(selector)
                if elements:
                    for i, element in enumerate(elements):
                        text = await element.inner_html()
                        if text and len(text.strip()) > 10:  # 过滤过短内容
                            clean_text = text.strip()
                            extracted_texts.append(clean_text)
                            selector_results.append({
                                'selector': selector,
                                'element_index': i,
                                'text_length': len(clean_text),
                                'text_preview': clean_text[:100] + "..." if len(clean_text) > 100 else clean_text
                            })
                            logger.debug(f"选择器 '{selector}' 第{i+1}个元素提取内容，长度: {len(clean_text)}")
            except Exception as e:
                logger.debug(f"选择器 '{selector}' 提取失败: {e}")
                continue

        # 记录提取结果到元数据
        await context.page.evaluate("""(results) => {
            window.extraction_results = results;
        }""", selector_results)

        # 根据组合策略处理内容
        if config.combine_strategy == "concat":
            return self._combine_content_concat(extracted_texts)
        elif config.combine_strategy == "separate":
            return self._combine_content_separate(extracted_texts, config.selectors)
        elif config.combine_strategy == "best":
            return self._combine_content_best(extracted_texts)
        else:
            logger.warning(f"未知的组合策略 '{config.combine_strategy}'，使用默认concat策略")
            return self._combine_content_concat(extracted_texts)

    def _combine_content_concat(self, texts: List[str]) -> str:
        """连接组合策略：将所有文本内容按顺序连接"""
        if not texts:
            return ""

        # 去重和清理
        cleaned_texts = []
        for text in texts:
            # 避免重复内容
            if not any(text in existing for existing in cleaned_texts):
                cleaned_texts.append(text)

        # 使用分隔符连接
        combined = "\n\n".join(cleaned_texts)
        logger.info(f"使用concat策略组合内容，共{len(cleaned_texts)}个片段，总长度: {len(combined)}")
        return combined

    def _combine_content_separate(self, texts: List[str], selectors: List[str]) -> str:
        """分离组合策略：按选择器分组内容"""
        if not texts:
            return ""

        combined = ""
        for i, text in enumerate(texts):
            selector_name = selectors[i % len(selectors)] if i < len(selectors) else f"section_{i+1}"
            combined += f"\n## {selector_name}\n\n{text}\n\n"

        logger.info(f"使用separate策略组合内容，共{len(texts)}个片段，总长度: {len(combined)}")
        return combined.strip()

    def _combine_content_best(self, texts: List[str]) -> str:
        """最佳组合策略：选择最长和内容最丰富的文本"""
        if not texts:
            return ""

        # 选择最长的文本作为主要内容
        best_text = max(texts, key=len)
        logger.info(f"使用best策略组合内容，选择最长文本，长度: {len(best_text)}")
        return best_text

    async def _extract_metadata(self, context: PlaywrightCrawlingContext, content: UrlContent):
        """提取页面元数据"""
        try:
            # 提取meta信息
            metadata = await context.page.evaluate("""
                () => {
                    const meta = {};

                    // 获取各种meta标签
                    const metaTags = document.querySelectorAll('meta[name], meta[property]');
                    metaTags.forEach(tag => {
                        const name = tag.getAttribute('name') || tag.getAttribute('property');
                        const value = tag.getAttribute('content');
                        if (name && value) {
                            meta[name] = value;
                        }
                    });

                    // 获取语言
                    meta.language = document.documentElement.lang || 'unknown';

                    // 获取页面大小信息
                    meta.scrollHeight = document.documentElement.scrollHeight;
                    meta.scrollWidth = document.documentElement.scrollWidth;

                    // 获取链接数量
                    meta.link_count = document.querySelectorAll('a').length;
                    meta.image_count = document.querySelectorAll('img').length;

                    return meta;
                }
            """)

            content.metadata = metadata

        except Exception as e:
            logger.warning(f"提取元数据时出错: {e}")
            content.metadata = {}

    def _detect_content_type(self, content: UrlContent) -> str:
        """检测内容类型"""
        if not content.html_content:
            return "unknown"

        # 检查是否是JSON
        try:
            json.loads(content.html_content)
            return "json"
        except:
            pass

        # 检查是否是XML
        if content.html_content.strip().startswith('<?xml'):
            return "xml"

        # 检查是否是HTML
        if '<html' in content.html_content.lower() or '<!doctype html' in content.html_content.lower():
            return "html"

        # 根据meta标签检测
        if content.metadata:
            content_type = content.metadata.get('Content-Type', '').lower()
            if 'json' in content_type:
                return "json"
            elif 'xml' in content_type:
                return "xml"
            elif 'html' in content_type:
                return "html"

        return "text"

    def _convert_to_markdown(self, html_content: str) -> str:
        """将 HTML 内容转换为 Markdown 格式"""
        try:
            if not html_content:
                return ""

            soup = BeautifulSoup(html_content, 'html.parser')
            for style in soup(["style"]):
                style.decompose()  # 移除 <style> 标签及其内容
            clean_html = str(soup)

            # 使用 markdownify 将 HTML 转换为 Markdown
            # 配置转换选项以优化输出
            markdown_content = md(
                html_content,
                # 转换选项
                heading_style="ATX",  # 使用 # 风格的标题
                bullets="-",  # 使用 - 作为列表符号
                strong_em_symbol="*",  # 使用 * 作为粗体斜体符号
                # 只指定要转换的标签，不指定 strip，让 markdownify 自动处理不需要的标签
                convert=['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                       'strong', 'em', 'b', 'i', 'u', 'a', 'img', 'ul', 'ol', 'li',
                       'blockquote', 'pre', 'code', 'table', 'thead', 'tbody',
                       'tr', 'th', 'td', 'br', 'hr']
            )

            # 清理多余的空行
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)

            # 移除开头和结尾的空白
            markdown_content = markdown_content.strip()

            logger.info(f"HTML 成功转换为 Markdown，长度: {len(markdown_content)}")
            return markdown_content

        except Exception as e:
            logger.error(f"HTML 转 Markdown 时出错: {e}")
            return ""

    async def save_content(self, content: UrlContent):
        """保存内容到文件"""
        try:
            # 保存Markdown内容
            md_filename = None
            if content.markdown_content:
                # 如果指定了输出文件名，使用指定的文件名；否则自动生成
                if self.output_filename:
                    # 确保文件名以 .md 结尾
                    if not self.output_filename.endswith('.md'):
                        md_filename = os.path.join(self.output_dir, self.output_filename + '.md')
                    else:
                        md_filename = os.path.join(self.output_dir, self.output_filename)
                else:
                    md_filename = self._generate_filename(content.url, "md")

                with open(md_filename, 'w', encoding='utf-8') as f:
                    f.write(content.markdown_content)
                logger.info(f"保存MD文件: {md_filename}")

            # 保存结构化数据
            # 如果指定了输出文件名，使用相同的文件名（仅扩展名不同）；否则自动生成
            if self.output_filename:
                json_filename = os.path.join(self.output_dir, self.output_filename + '.json')
            else:
                json_filename = self._generate_filename(content.url, "json")
            content_data = {
                "url": content.url,
                "title": content.title,
                "markdown_content": content.markdown_content,  # 添加完整的 markdown 内容
                "timestamp": content.timestamp,
                "content_type": content.content_type,
                "status_code": content.status_code,
                "error_message": content.error_message,
                "metadata": content.metadata,
                "files": {
                    "md_file": md_filename,
                    "json_file": json_filename
                },
                "success": getattr(content, 'success', False)
            }

            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            logger.info(f"保存JSON文件: {json_filename}")
            return json_filename, md_filename

        except Exception as e:
            logger.error(f"保存内容失败: {e}")
            return None, None

    async def request_handler(self, context: PlaywrightCrawlingContext) -> None:
        """请求处理器"""
        url = context.request.url
        logger.info(f"处理URL: {url}")

        # 设置页面默认导航超时时间（解决 Page.goto 超时问题）
        context.page.set_default_navigation_timeout(self.wait_timeout * 1000)
        logger.debug(f"设置页面导航超时: {self.wait_timeout} 秒")

        result_data = {}
        try:
            # 提取页面内容
            content = await self.extract_page_content(context)

            # 保存内容
            json_file, md_file = await self.save_content(content)

            result = {
                "url": url,
                "success": getattr(content, 'success', False),
                "title": content.title,
                "content_type": content.content_type,
                "md_file": md_file,
                "json_file": json_file,
                "timestamp": content.timestamp
            }
            # 推送数据到结果队列
            result_data.update(result)
            await context.push_data(result)
            await self.result_summary(result_data)

        except Exception as e:
            logger.error(f"处理URL时发生错误: {e}")
            result = {
                "url": url,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            result_data.update(result)
            await context.push_data(result)
            await self.result_summary(result_data)

    async def result_summary(self, result: Dict[str, Any]):
        logger.info("=== 提取结果 ===")
        if result.get("success"):
            logger.info(f"✅ 成功提取URL内容")
            logger.info(f"标题: {result.get('title', 'N/A')}")
            logger.info(f"内容类型: {result.get('content_type', 'N/A')}")
            if result.get("json_file"):
                # 读取JSON文件以显示更详细的信息
                try:
                    with open(result["json_file"], 'r', encoding='utf-8') as f:
                        json_data = json.load(f)

                    metadata = json_data.get('metadata', {})
                    extraction_method = metadata.get('extraction_method', 'unknown')
                    extractor_config = metadata.get('extractor_config', 'none')

                    logger.info(f"提取方法: {extraction_method}")
                    if extractor_config != 'none':
                        logger.info(f"使用配置: {extractor_config}")

                except Exception as e:
                    logger.debug(f"读取结果JSON失败: {e}")

            if result.get("html_file"):
                logger.info(f"HTML文件: {result['html_file']}")
            if result.get("json_file"):
                logger.info(f"JSON文件: {result['json_file']}")
        else:
            logger.error(f"❌ 提取失败: {result.get('error', 'Unknown error')}")

    async def extract_url(self, url: str) -> Dict[str, Any]:
        """提取单个URL的内容"""
        logger.info(f"开始提取URL内容: {url}")
        try:
            # 运行爬虫
            await self.crawler.run([url])
        except Exception as e:
            logger.error(f"提取URL内容失败: {e}")
            return {"success": False, "error": str(e)}


async def extract_url_content(url: str, output_dir: str = "html",
                             headless: bool = True, timeout: int = 60,
                             selector_config_file: Optional[str] = None,
                             output_filename: Optional[str] = None):
    """便捷函数：提取单个URL的内容

    Args:
        url: 要提取的URL
        output_dir: 输出目录
        headless: 是否使用无头模式
        timeout: 超时时间（秒）
        selector_config_file: URL选择器配置文件路径
        output_filename: 输出文件名（不含扩展名），不指定时自动生成

    Returns:
        提取结果的字典
    """
    extractor = UrlContentExtractor(
        output_dir=output_dir,
        wait_timeout=timeout,
        headless=headless,  # 直接传递 headless 参数
        selector_config_file=selector_config_file,
        output_filename=output_filename  # 传递输出文件名参数
    )

    await extractor.extract_url(url)


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='URL内容提取工具')
    parser.add_argument('url', help='要提取内容的URL')
    parser.add_argument('--output-dir', '-o', default='urls', help='输出目录 (默认: urls)')
    parser.add_argument('--output-filename', '-f', default=None,
                       help='输出文件名（不含扩展名），不指定时自动生成 (默认: None)')
    parser.add_argument('--headless', action='store_true', default=True, help='使用无头模式 (默认: True)')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='显示浏览器窗口')
    parser.add_argument('--timeout', '-t', type=int, default=60, help='超时时间(秒) (默认: 30)')
    parser.add_argument('--config', '-c', default="url_selector_config_default.json",
                       help='URL选择器配置文件路径 (可选，默认使用默认配置)')

    args = parser.parse_args()

    logger.info("=== URL内容提取工具 ===")
    logger.info(f"目标URL: {args.url}")
    logger.info(f"输出目录: {args.output_dir}")
    logger.info(f"输出文件名: {args.output_filename if args.output_filename else '自动生成'}")
    logger.info(f"无头模式: {args.headless}")
    logger.info(f"超时时间: {args.timeout}秒")
    logger.info(f"配置文件: {args.config}")

    await extract_url_content(
        url=args.url,
        output_dir=args.output_dir,
        output_filename=args.output_filename,
        headless=args.headless,
        timeout=args.timeout,
        selector_config_file=args.config
    )

if __name__ == '__main__':
    asyncio.run(main())
