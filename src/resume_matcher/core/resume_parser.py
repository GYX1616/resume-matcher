from __future__ import annotations

"""简历解析编排 - 文件解析 + AI 结构化提取"""

from pathlib import Path

from resume_matcher.ai.client import create_client, generate_structured
from resume_matcher.ai.prompts import build_resume_parse_prompt
from resume_matcher.ai.schemas import RESUME_SCHEMA
from resume_matcher.core.models import Resume
from resume_matcher.parsers.base import get_parser


def parse_resume(
    file_path: Path,
    model_name: str = "deepseek-chat",
    api_key: str = "",
    base_url: str = "https://api.deepseek.com",
) -> Resume:
    """解析简历文件，返回结构化简历数据

    流程：
    1. 根据文件类型提取纯文本
    2. 调用 AI 进行结构化信息提取
    3. 校验并返回 Resume 对象
    """
    # Step 1: 提取文本
    parser = get_parser(file_path)
    raw_text = parser.parse(file_path)

    if not raw_text.strip():
        raise ValueError(f"无法从文件中提取文本内容: {file_path}")

    # Step 2: AI 结构化提取
    client = create_client(api_key=api_key, base_url=base_url)
    prompt = build_resume_parse_prompt(raw_text)

    try:
        data = generate_structured(
            client=client,
            model=model_name,
            prompt=prompt,
            json_schema=RESUME_SCHEMA,
            temperature=0.1,
        )
    except Exception as e:
        raise RuntimeError(f"AI 简历解析失败: {e}") from e

    # Step 3: 构建 Resume 对象
    resume = Resume.model_validate(data)
    resume.raw_text = raw_text
    return resume
