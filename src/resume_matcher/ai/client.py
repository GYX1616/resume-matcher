"""DeepSeek API 客户端封装（兼容 OpenAI SDK）"""

from __future__ import annotations

import json

from openai import OpenAI


def create_client(
    api_key: str,
    base_url: str = "https://api.deepseek.com",
) -> OpenAI:
    """创建 DeepSeek API 客户端"""
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_structured(
    client: OpenAI,
    model: str,
    prompt: str,
    json_schema: dict,
    temperature: float = 0.1,
) -> dict:
    """调用 DeepSeek 生成结构化 JSON 输出

    Args:
        client: OpenAI 兼容客户端
        model: 模型名称
        prompt: 提示词
        json_schema: 期望的 JSON Schema（嵌入到 system prompt 中）
        temperature: 温度参数

    Returns:
        解析后的 dict
    """
    schema_str = json.dumps(json_schema, ensure_ascii=False, indent=2)
    system_msg = (
        "你是一个专业的 JSON 数据提取助手。"
        "请严格按照以下 JSON Schema 格式输出，不要添加任何额外文字或 markdown 标记。\n\n"
        f"JSON Schema:\n{schema_str}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return json.loads(content)
