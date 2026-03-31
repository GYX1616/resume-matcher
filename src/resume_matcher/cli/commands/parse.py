"""parse 命令 - 仅解析简历"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from resume_matcher.core.config import get_settings
from resume_matcher.core.resume_parser import parse_resume

console = Console()


def parse(
    resume_file: Path = typer.Argument(..., help="简历文件路径（PDF/DOCX/TXT）", exists=True),
    model: str = typer.Option(None, "--model", help="DeepSeek 模型名"),
    output_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """解析简历文件，提取结构化信息"""
    settings = get_settings()

    if not settings.deepseek_api_key:
        console.print("[red]错误: DeepSeek API Key 未配置[/red]")
        console.print("请运行: resume-matcher config set deepseek_api_key sk-xxx")
        raise typer.Exit(1)

    model_name = model or settings.deepseek_model

    with console.status("正在解析简历...", spinner="dots"):
        resume = parse_resume(
            resume_file,
            model_name=model_name,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    if output_json:
        console.print_json(json.dumps(resume.model_dump(), ensure_ascii=False, indent=2))
        return

    # 表格展示
    console.print(Panel(f"[bold]{resume.name}[/bold]", title="简历解析结果"))

    if resume.email or resume.phone or resume.location:
        console.print(f"  邮箱: {resume.email}  电话: {resume.phone}  地点: {resume.location}")

    if resume.summary:
        console.print(f"\n[bold]个人简介:[/bold] {resume.summary}")

    if resume.education:
        table = Table(title="教育经历")
        table.add_column("学校")
        table.add_column("学历")
        table.add_column("专业")
        table.add_column("时间")
        for edu in resume.education:
            table.add_row(edu.school, edu.degree, edu.major, f"{edu.start_date} - {edu.end_date}")
        console.print(table)

    if resume.work_experience:
        table = Table(title="工作经历")
        table.add_column("公司")
        table.add_column("职位")
        table.add_column("时间")
        table.add_column("描述", max_width=40)
        for exp in resume.work_experience:
            table.add_row(
                exp.company, exp.title, f"{exp.start_date} - {exp.end_date}", exp.description[:80]
            )
        console.print(table)

    if resume.skills:
        console.print(f"\n[bold]技能:[/bold] {', '.join(resume.skills)}")

    if resume.certifications:
        console.print(f"[bold]证书:[/bold] {', '.join(resume.certifications)}")
