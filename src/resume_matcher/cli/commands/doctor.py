"""doctor 命令 - 环境健康检查"""

from rich.console import Console

from resume_matcher.core.config import get_settings

console = Console()


def doctor() -> None:
    """检查运行环境（DeepSeek API 连接、模型可用性）"""
    settings = get_settings()

    console.print("[bold]环境检查[/bold]\n")

    # 检查 API Key
    if not settings.deepseek_api_key:
        console.print("  [red]DeepSeek API Key 未配置[/red]")
        console.print("  请在 .env 文件中设置 DEEPSEEK_API_KEY")
        console.print("  或设置环境变量: export DEEPSEEK_API_KEY=sk-xxx")
        console.print()
        return

    console.print(f"  API URL: {settings.deepseek_base_url}")
    console.print(f"  模型: {settings.deepseek_model}")
    console.print(f"  API Key: {settings.deepseek_api_key[:8]}...{settings.deepseek_api_key[-4:]}")

    # 检查 API 连接
    try:
        from resume_matcher.ai.client import create_client

        client = create_client(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        console.print("  [green]DeepSeek API 连接正常[/green]")

        if model_ids:
            console.print(f"  可用模型: {', '.join(model_ids)}")

    except Exception as e:
        console.print(f"  [red]DeepSeek API 连接失败: {e}[/red]")
        console.print("  请检查 API Key 和网络连接")

    console.print()
