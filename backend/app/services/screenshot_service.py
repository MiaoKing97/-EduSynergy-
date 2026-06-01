import base64
import logging
import asyncio
import re
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def _trigger_lazy_load(page):
    """
    对抗骨架屏与懒加载辅助函数
    """
    logger.info("   -> 模拟滚动到底部以触发懒加载...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(4000)
    logger.info("   -> 恢复滚动到顶部，对齐截图排版...")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)


def _capture_sync(url: str = None, html_content: str = None):
    """
    在独立线程中运行的同步截图与源码清洗提纯双能引擎
    支持：1. 在线 URL 爬取渲染  2. 本地纯 HTML 源码内存直接渲染
    """
    # 🌟 核心防御：前置参数校验，防止传入空参数导致崩溃
    if html_content:
        logger.info("🎭 [Browser] 检测到本地文件上传模式，启动源码内存直接渲染引擎")
    elif url:
        logger.info(f"🎭 [Browser] 启动无头浏览器抓取在线 URL: {url}")
        if not url.startswith("http"):
            url = "http://" + url
    else:
        raise ValueError("🚨 传入无头浏览器的 URL 和 HTML 内容不能同时为空！")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # 1. 渲染 PC 端视图 (1280px)
            logger.info("💻 [Browser] 正在渲染 PC 端视图...")
            page_pc = browser.new_page(viewport={"width": 1280, "height": 800})

            if html_content:
                page_pc.set_content(html_content, wait_until="load")
            elif url:
                page_pc.goto(url, wait_until="load", timeout=60000)

            _trigger_lazy_load(page_pc)
            pc_bytes = page_pc.screenshot(full_page=True)

            # 如果是在线抓取模式，现场洗出一份提纯源码；如果是文件上传模式，直接使用原码
            if not html_content:
                logger.info("📄 [Browser] 正在提取并清洗在线网页 DOM 结构源码...")
                raw_html = page_pc.evaluate('''() => {
                    let clone = document.documentElement.cloneNode(true);
                    clone.querySelectorAll('script, noscript, style, iframe, canvas, video, audio, svg').forEach(el => el.remove());
                    clone.querySelectorAll('img').forEach(el => {
                        if (el.src && el.src.startsWith('data:image')) {
                            el.src = 'data:image/hidden_to_save_tokens';
                        }
                    });
                    return clone.innerHTML;
                }''')
                # 修复潜在的空正则替换警告，改为简单的清除空白或者保留原有逻辑
                clean_html = re.sub(r'', '', raw_html, flags=re.DOTALL).strip()
            else:
                clean_html = html_content

            # 2. 渲染移动端视图 (375px)
            logger.info("📱 [Browser] 正在渲染移动端视图...")
            page_mobile = browser.new_page(viewport={"width": 375, "height": 812})

            if html_content:
                page_mobile.set_content(html_content, wait_until="load")
            elif url:
                page_mobile.goto(url, wait_until="load", timeout=60000)

            _trigger_lazy_load(page_mobile)
            mobile_bytes = page_mobile.screenshot(full_page=True)

            logger.info("📸 [Browser] 双端快照及源码解析加工流抓取完成")
            return {
                "pc_snapshot": base64.b64encode(pc_bytes).decode('utf-8'),
                "mobile_snapshot": base64.b64encode(mobile_bytes).decode('utf-8'),
                "source_code": clean_html
            }
        except Exception as e:
            logger.error(f"❌ [Browser] 核心渲染阶段失败: {str(e)}")
            raise e
        finally:
            browser.close()
            logger.info("🏁 [Browser] 浏览器无头容器资源已回收")


async def capture_responsive_screenshots(url: str = None, html_content: str = None):
    """
    利用 asyncio.to_thread 投递至独立线程，保障 FastAPI 事件循环高并发不卡死
    """
    return await asyncio.to_thread(_capture_sync, url, html_content)