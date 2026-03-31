from __future__ import annotations

"""浏览器自动化基类 - Playwright 共享逻辑"""

import json
import logging
import random
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cookie 持久化目录
COOKIE_DIR = Path.home() / ".resume-matcher" / "cookies"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)


def get_cookie_path(platform: str) -> Path:
    """获取平台 Cookie 文件路径"""
    return COOKIE_DIR / f"{platform}_cookies.json"


def save_cookies(page, platform: str) -> None:
    """保存浏览器 Cookie 到本地文件"""
    cookies = page.context.cookies()
    cookie_path = get_cookie_path(platform)
    cookie_path.write_text(json.dumps(cookies, ensure_ascii=False), encoding="utf-8")
    logger.info("已保存 %d 条 Cookie 到 %s", len(cookies), cookie_path)


def load_cookies(context, platform: str) -> bool:
    """从本地文件加载 Cookie，返回是否成功"""
    cookie_path = get_cookie_path(platform)
    if not cookie_path.exists():
        return False
    try:
        cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
        context.add_cookies(cookies)
        logger.info("已加载 %d 条 Cookie", len(cookies))
        return True
    except Exception as e:
        logger.warning("加载 Cookie 失败: %s", e)
        return False


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """随机等待，模拟人工操作节奏"""
    time.sleep(random.uniform(min_sec, max_sec))


STEALTH_JS = """
() => {
    // 隐藏 navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // 模拟正常的 plugins 数量
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // 模拟正常的 languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-CN', 'zh', 'en'],
    });

    // 覆盖 chrome runtime
    window.chrome = { runtime: {} };
}
"""

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def create_browser_context(
    playwright,
    platform: str,
    headless: bool = False,
    user_agent: Optional[str] = None,
):
    """创建带有反检测配置的浏览器上下文

    Args:
        playwright: Playwright 实例
        platform: 平台名（用于 Cookie 持久化）
        headless: 是否无头模式（首次登录需设为 False）
        user_agent: 自定义 User-Agent

    Returns:
        (browser, context, page) 三元组
    """
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
        ],
    )

    context = browser.new_context(
        user_agent=user_agent or DEFAULT_USER_AGENT,
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )

    # 加载持久化 Cookie
    load_cookies(context, platform)

    page = context.new_page()

    # 注入反检测脚本
    page.add_init_script(STEALTH_JS)

    return browser, context, page


def wait_for_login(page, check_selector: str, platform: str, timeout: int = 120) -> bool:
    """等待用户手动登录

    Args:
        page: Playwright page
        check_selector: 登录成功后会出现的元素选择器
        platform: 平台名
        timeout: 超时时间（秒）

    Returns:
        是否登录成功
    """
    logger.info("请在浏览器中手动登录 %s...", platform)
    try:
        page.wait_for_selector(check_selector, timeout=timeout * 1000)
        save_cookies(page, platform)
        logger.info("%s 登录成功!", platform)
        return True
    except Exception:
        logger.error("%s 登录超时", platform)
        return False
