from __future__ import annotations

"""scan 命令 - 简历解析 + 岗位匹配"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from resume_matcher.core.config import get_settings
from resume_matcher.core.matcher import match_jobs
from resume_matcher.core.models import SearchCriteria
from resume_matcher.core.resume_parser import parse_resume
from resume_matcher.cli.display import render_match_results
from resume_matcher.platforms.registry import get_all_jobs

console = Console()


def scan(
    resume_file: Path = typer.Argument(..., help="简历文件路径（PDF/DOCX/TXT）", exists=True),
    title: str = typer.Option("", "-t", "--title", help="目标岗位名称"),
    location: str = typer.Option("", "-l", "--location", help="期望工作地点"),
    keywords: list[str] = typer.Option([], "-k", "--keywords", help="额外关键词"),
    platform: str = typer.Option("all", "-p", "--platform", help="平台筛选: boss|zhilian|liepin|lagou|job51|all"),
    top_n: int = typer.Option(None, "-n", "--top-n", help="展示结果数量"),
    min_score: float = typer.Option(0, "-s", "--min-score", help="最低匹配分数"),
    model: str = typer.Option(None, "--model", help="DeepSeek 模型名"),
    real: bool = typer.Option(False, "--real", help="使用真实平台数据（Playwright 浏览器自动化）"),
    headless: bool = typer.Option(False, "--headless", help="浏览器无头模式（需已登录保存 Cookie）"),
    output_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="显示详细匹配分析"),
) -> None:
    """扫描岗位并匹配简历，展示最匹配的岗位列表"""
    settings = get_settings()

    if not settings.deepseek_api_key:
        console.print("[red]错误: DeepSeek API Key 未配置[/red]")
        console.print("请运行: resume-matcher config set deepseek_api_key sk-xxx")
        raise typer.Exit(1)

    model_name = model or settings.deepseek_model
    n = top_n or settings.default_top_n

    criteria = SearchCriteria(
        job_title=title,
        keywords=keywords,
        location=location,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: 解析简历
        task = progress.add_task("正在解析简历...", total=None)
        resume = parse_resume(
            resume_file,
            model_name=model_name,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        progress.update(task, description="[green]简历解析完成")

        # Step 2: 获取岗位数据
        progress.update(task, description="正在获取岗位数据...")
        platform_filter = None if platform == "all" else platform
        jobs = get_all_jobs(criteria, platform_filter=platform_filter, use_real=real, headless=headless)
        progress.update(task, description=f"[green]获取到 {len(jobs)} 个岗位")

        # Step 3: AI 匹配
        progress.update(task, description="正在进行智能匹配...")
        results = match_jobs(
            resume=resume,
            jobs=jobs,
            criteria=criteria,
            model_name=model_name,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        progress.update(task, description="[green]匹配完成")

    # 过滤和排序
    results = [r for r in results if r.score >= min_score]
    results = results[:n]

    if not results:
        console.print("[yellow]没有找到匹配的岗位。请尝试调整搜索条件。[/yellow]")
        return

    if output_json:
        data = [r.model_dump() for r in results]
        console.print_json(json.dumps(data, ensure_ascii=False, indent=2))
        return

    render_match_results(console, results, verbose=verbose)
