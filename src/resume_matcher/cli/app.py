"""CLI 应用入口"""

import typer

from resume_matcher import __version__

app = typer.Typer(
    name="resume-matcher",
    help="智能岗位匹配工具 - 帮助求职者找到最匹配的工作岗位",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"resume-matcher v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", help="显示版本号", callback=version_callback, is_eager=True
    ),
) -> None:
    """智能岗位匹配工具"""


# 延迟导入命令，避免循环依赖
from resume_matcher.cli.commands.parse import parse  # noqa: E402
from resume_matcher.cli.commands.scan import scan  # noqa: E402
from resume_matcher.cli.commands.config import config_app  # noqa: E402
from resume_matcher.cli.commands.doctor import doctor  # noqa: E402
from resume_matcher.cli.commands.login import login  # noqa: E402

app.command()(parse)
app.command()(scan)
app.command()(login)
app.add_typer(config_app, name="config", help="查看和修改配置")
app.command()(doctor)
