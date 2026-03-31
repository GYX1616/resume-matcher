from __future__ import annotations

"""login 命令 - 登录招聘平台并保存 Cookie"""

import typer
from rich.console import Console

console = Console()

SUPPORTED_PLATFORMS = {
    "boss": ("Boss直聘", "https://www.zhipin.com", ".user-info, .user-nav"),
    "liepin": ("猎聘", "https://www.liepin.com", ".user-info, .header-user"),
    "job51": ("前程无忧", "https://we.51job.com", ".user-info, .uname"),
}


def login(
    platform: str = typer.Argument(
        ...,
        help="平台名称: boss | liepin | job51",
    ),
) -> None:
    """登录招聘平台并保存 Cookie，后续使用 --real 模式时无需重复登录"""
    if platform not in SUPPORTED_PLATFORMS:
        console.print(f"[red]不支持的平台: {platform}[/red]")
        console.print(f"支持的平台: {', '.join(SUPPORTED_PLATFORMS.keys())}")
        raise typer.Exit(1)

    name, url, check_selector = SUPPORTED_PLATFORMS[platform]
    console.print(f"正在打开 {name} 登录页面...")
    console.print("[yellow]请在浏览器中完成登录，登录成功后 Cookie 将自动保存。[/yellow]")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        console.print("[red]请先安装 Playwright: pip install playwright && playwright install chromium[/red]")
        raise typer.Exit(1)

    from resume_matcher.platforms.browser_base import (
        create_browser_context,
        save_cookies,
        wait_for_login,
    )

    with sync_playwright() as pw:
        browser, context, page = create_browser_context(
            pw, platform, headless=False
        )
        try:
            page.goto(url, wait_until="domcontentloaded")

            logged_in = wait_for_login(
                page,
                check_selector=check_selector,
                platform=name,
                timeout=180,
            )

            if logged_in:
                save_cookies(page, platform)
                console.print(f"[green]✅ {name} 登录成功，Cookie 已保存！[/green]")
                console.print("后续使用 [bold]--real[/bold] 模式时将自动加载 Cookie。")
            else:
                console.print(f"[red]❌ {name} 登录超时。[/red]")
        finally:
            browser.close()
