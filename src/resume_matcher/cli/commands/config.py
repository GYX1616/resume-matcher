"""config 命令 - 查看和修改配置"""

import typer
from rich.console import Console
from rich.table import Table

from resume_matcher.core.config import get_settings

config_app = typer.Typer()
console = Console()


@config_app.command("show")
def config_show() -> None:
    """显示当前配置"""
    settings = get_settings()

    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    api_key_display = f"{settings.deepseek_api_key[:8]}...{settings.deepseek_api_key[-4:]}" if settings.deepseek_api_key else "未设置"
    table.add_row("DeepSeek API Key", api_key_display)
    table.add_row("DeepSeek URL", settings.deepseek_base_url)
    table.add_row("模型", settings.deepseek_model)
    table.add_row("默认结果数", str(settings.default_top_n))
    table.add_row("默认平台", settings.default_platform)

    console.print(table)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="配置项: deepseek_api_key, deepseek_base_url, deepseek_model, default_top_n, default_platform"),
    value: str = typer.Argument(..., help="配置值"),
) -> None:
    """设置配置项（写入 .env 文件）"""
    valid_keys = {"deepseek_api_key", "deepseek_base_url", "deepseek_model", "default_top_n", "default_platform"}
    if key not in valid_keys:
        console.print(f"[red]无效的配置项: {key}[/red]")
        console.print(f"可用配置项: {', '.join(sorted(valid_keys))}")
        raise typer.Exit(1)

    env_key = key.upper()
    env_file = ".env"

    # 读取现有 .env 内容
    lines: list[str] = []
    found = False
    try:
        with open(env_file) as f:
            for line in f:
                if line.strip().startswith(f"{env_key}="):
                    lines.append(f"{env_key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    except FileNotFoundError:
        pass

    if not found:
        lines.append(f"{env_key}={value}\n")

    with open(env_file, "w") as f:
        f.writelines(lines)

    console.print(f"[green]已设置 {key} = {value}[/green]")
