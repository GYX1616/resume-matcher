"""应用配置管理"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，支持环境变量和 .env 文件"""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    default_top_n: int = 10
    default_platform: str = "all"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
