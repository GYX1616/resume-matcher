from __future__ import annotations

"""Rich 表格渲染"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from resume_matcher.core.models import MatchResult


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _format_salary(min_k: int, max_k: int) -> str:
    if min_k and max_k:
        return f"{min_k}K-{max_k}K"
    if min_k:
        return f"{min_k}K+"
    if max_k:
        return f"~{max_k}K"
    return "面议"


def render_match_results(
    console: Console,
    results: list[MatchResult],
    verbose: bool = False,
) -> None:
    """渲染匹配结果表格"""
    table = Table(title=f"岗位匹配结果（共 {len(results)} 条）")
    table.add_column("#", style="dim", width=3)
    table.add_column("匹配度", justify="center", width=7)
    table.add_column("岗位名称", min_width=15)
    table.add_column("公司", min_width=10)
    table.add_column("薪资", width=12)
    table.add_column("地点", width=10)
    table.add_column("平台", width=6)

    if not verbose:
        table.add_column("匹配原因", min_width=20)

    platform_names = {"boss": "Boss", "zhilian": "智联", "liepin": "猎聘", "lagou": "拉勾", "job51": "前程"}
    for i, result in enumerate(results, 1):
        color = _score_color(result.score)
        salary = _format_salary(result.job.salary.min_k, result.job.salary.max_k)
        platform_display = platform_names.get(result.job.platform.value, result.job.platform.value)

        # 岗位名称带链接（终端支持的链接格式）
        title_display = result.job.title
        if result.job.url:
            title_display = f"[link={result.job.url}]{result.job.title}[/link]"

        row = [
            str(i),
            f"[{color}]{result.score:.0f}分[/{color}]",
            title_display,
            result.job.company,
            salary,
            result.job.location,
            platform_display,
        ]

        if not verbose:
            reason = result.match_reasons[0] if result.match_reasons else ""
            row.append(reason)

        table.add_row(*row)

    console.print(table)

    # verbose 模式下展示每条岗位的详细分析
    if verbose:
        for i, result in enumerate(results, 1):
            color = _score_color(result.score)
            header = f"[{color}]{result.score:.0f}分[/{color}] {result.job.title} @ {result.job.company}"
            lines = []
            if result.match_reasons:
                lines.append("[bold]匹配原因:[/bold]")
                for reason in result.match_reasons:
                    lines.append(f"  • {reason}")
            if result.skill_overlap:
                lines.append(f"[bold]技能重合:[/bold] {', '.join(result.skill_overlap)}")
            if result.gaps:
                lines.append(f"[bold]缺失项:[/bold] {', '.join(result.gaps)}")
            if result.job.url:
                lines.append(f"[bold]链接:[/bold] [link={result.job.url}]{result.job.url}[/link]")
            console.print(Panel("\n".join(lines), title=f"#{i} {header}"))
