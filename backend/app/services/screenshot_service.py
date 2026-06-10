"""
Screenshot service — Playwright runs in a dedicated long-lived worker thread.

The browser process is owned entirely by a background thread.  All calls to
Playwright (launch, screenshot, evaluate) go through a request queue so they
never cross thread boundaries.

On Windows the asyncio ProactorEventLoop doesn't support async subprocess
creation, so we must avoid the async Playwright API.  This design sidesteps
the problem cleanly.
"""
import asyncio
import base64
import logging
import queue
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class _BrowserWorker:
    """Runs in a dedicated background thread. Owns the Playwright Browser."""

    def __init__(self):
        self._browser = None
        self._queue: queue.Queue = queue.Queue()
        self._shutdown = threading.Event()

    # ── Public API (call from ANY thread via self._queue) ──────────────

    def start(self):
        """Start Playwright browser. Must be called from the worker thread."""
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        self._browser = pw.chromium.launch(headless=True)
        logger.info("🎭 [Browser] Persistent Chromium launched (worker thread)")
        self._pw = pw          # keep reference so it doesn't get GC'd

    def capture(
        self,
        url: Optional[str] = None,
        html_content: Optional[str] = None,
        pc_width: int = 1280,
        pc_height: int = 800,
        mobile_width: int = 375,
        mobile_height: int = 812,
    ) -> dict:
        """Run in the worker thread."""
        if html_content:
            logger.info("🎭 [Browser] Local HTML source mode")
        elif url:
            logger.info(f"🎭 [Browser] URL mode: {url}")
            if not url.startswith("http"):
                url = "http://" + url
        else:
            raise ValueError("URL and HTML content cannot both be empty")

        browser = self._browser

        # --- PC screenshot ---
        logger.info("💻 [Browser] Rendering PC view...")
        ctx = browser.new_context(viewport={"width": pc_width, "height": pc_height})
        page = ctx.new_page()
        try:
            if html_content:
                page.set_content(html_content, wait_until="load")
            else:
                page.goto(url, wait_until="load", timeout=60000)
            self._lazy_load(page)
            pc_bytes = page.screenshot(full_page=True)

            if not html_content:
                logger.info("📄 [Browser] Extracting cleaned DOM...")
                raw_html = page.evaluate('''() => {
                    let clone = document.documentElement.cloneNode(true);
                    clone.querySelectorAll('script, noscript, style, iframe, canvas, video, audio, svg').forEach(el => el.remove());
                    clone.querySelectorAll('img').forEach(el => {
                        if (el.src && el.src.startsWith('data:image')) {
                            el.src = 'data:image/hidden_to_save_tokens';
                        }
                    });
                    return clone.innerHTML;
                }''')
                clean_html = raw_html.strip()
            else:
                clean_html = html_content
        finally:
            page.close()
            ctx.close()

        # --- Mobile screenshot ---
        logger.info("📱 [Browser] Rendering mobile view...")
        ctx = browser.new_context(viewport={"width": mobile_width, "height": mobile_height})
        page = ctx.new_page()
        try:
            if html_content:
                page.set_content(html_content, wait_until="load")
            else:
                page.goto(url, wait_until="load", timeout=60000)
            self._lazy_load(page)
            mobile_bytes = page.screenshot(full_page=True)
        finally:
            page.close()
            ctx.close()

        logger.info("📸 [Browser] Dual-view capture complete")
        return {
            "pc_snapshot": base64.b64encode(pc_bytes).decode('utf-8'),
            "mobile_snapshot": base64.b64encode(mobile_bytes).decode('utf-8'),
            "source_code": clean_html,
        }

    def close(self):
        """Run in the worker thread."""
        if self._browser:
            self._browser.close()
            logger.info("🏁 [Browser] Persistent Chromium closed")
        if hasattr(self, '_pw'):
            self._pw.stop()

    @staticmethod
    def _lazy_load(page):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

    # ── Internal: message loop (runs in worker thread) ────────────────

    def _loop(self):
        self.start()
        while not self._shutdown.is_set():
            try:
                future, args = self._queue.get(timeout=1)
            except queue.Empty:
                continue
            try:
                future.set_result(self.capture(**args))
            except Exception as exc:
                future.set_exception(exc)

    def submit(self, **kwargs) -> "concurrent.futures.Future":
        """Submit a capture job from any thread. Returns a Future."""
        import concurrent.futures
        future: "concurrent.futures.Future" = concurrent.futures.Future()
        self._queue.put((future, kwargs), timeout=60)
        return future

    def stop(self):
        """Signal the worker to shut down after finishing current work."""
        self._shutdown.set()


class PersistentBrowser:
    """Singleton — owns a background thread that runs Playwright."""

    _instance: Optional["PersistentBrowser"] = None
    _lock = threading.Lock()
    _worker: Optional[_BrowserWorker] = None
    _thread: Optional[threading.Thread] = None

    def __init__(self):
        self._worker = _BrowserWorker()
        self._thread = threading.Thread(target=self._worker._loop, daemon=True, name="playwright-worker")
        self._thread.start()
        logger.info("🎭 [Browser] Singleton PersistentBrowser worker thread started")

    @classmethod
    def get(cls) -> "PersistentBrowser":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def capture(self, **kwargs) -> dict:
        """Submit work to the worker thread and wait for result."""
        future = self._worker.submit(**kwargs)
        return future.result(timeout=120)

    @classmethod
    def cleanup(cls):
        """Shutdown worker thread. Call once on app shutdown."""
        if cls._worker is not None:
            cls._worker.stop()
            if cls._thread is not None:
                cls._thread.join(timeout=10)
        cls._instance = None
        cls._worker = None
        cls._thread = None


def capture_responsive_screenshots(url: str = None, html_content: str = None) -> dict:
    """Sync entry point. Call from async routes via ``await asyncio.to_thread(...)``."""
    browser = PersistentBrowser.get()
    return browser.capture(url=url, html_content=html_content)


def cleanup_browser():
    """Sync wrapper for shutdown."""
    PersistentBrowser.cleanup()