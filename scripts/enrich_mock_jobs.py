"""一次性脚本：用 DeepSeek 批量扩充 mock_jobs.json 的岗位描述"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

MOCK_JOBS_PATH = Path(__file__).resolve().parent.parent / "src" / "resume_matcher" / "data" / "mock_jobs.json"

ENRICH_PROMPT = """你是一个资深的 HR 招聘专家。请根据以下岗位基本信息，生成一份真实、详细的岗位 JD（Job Description）。

## 岗位基本信息

- 岗位名称：{title}
- 公司行业：{industry}
- 公司规模：{company_size}
- 经验要求：{experience_required}
- 学历要求：{education_required}
- 当前简要描述：{description}
- 当前要求：{requirements}

## 输出要求

请以 JSON 格式输出以下字段：

1. **description**（string）：200-400 字的详细职位描述，包含：
   - 岗位概述（1-2句话说明该岗位在团队中的定位）
   - 岗位职责（5-8 条具体工作内容，每条 20-40 字）
   - 工作挑战与亮点（1-2 句话说明技术挑战或成长空间）

2. **must_have_skills**（array of string）：必须具备的技能/经验（5-8 条），每条简洁明了

3. **nice_to_have_skills**（array of string）：加分项技能/经验（3-5 条）

4. **seniority_level**（string）：岗位资历等级，只能是以下之一：
   - "junior"（初级，0-2年经验）
   - "mid"（中级，2-5年经验）
   - "senior"（高级，5-10年经验）
   - "lead"（技术负责人/管理者，8年以上）

5. **job_category**（string）：岗位大类，只能是以下之一：
   - "backend"（后端开发）
   - "frontend"（前端开发）
   - "fullstack"（全栈开发）
   - "data"（数据分析/数据工程）
   - "ai"（AI/算法/机器学习）
   - "devops"（运维/DevOps）
   - "test"（测试）
   - "security"（安全）
   - "pm"（产品经理/项目经理）
   - "design"（设计）

请确保内容真实可信，符合中国互联网行业的招聘习惯。直接输出 JSON，不要添加 markdown 标记。"""


def enrich_jobs():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        # Try reading from .env
        # .env is at project root: resume-matcher/.env
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in environment or .env file")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Load mock data
    with open(MOCK_JOBS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    jobs = data["jobs"]

    # Group by unique (title, description) to avoid redundant API calls
    combos: dict[tuple[str, str], list[int]] = {}
    for idx, job in enumerate(jobs):
        key = (job["title"], job["description"])
        combos.setdefault(key, []).append(idx)

    print(f"Total jobs: {len(jobs)}, unique combos: {len(combos)}")

    enriched_count = 0
    for (title, desc), indices in combos.items():
        # Use first job as representative
        rep = jobs[indices[0]]
        print(f"\n[{enriched_count + 1}/{len(combos)}] Enriching: {title} ...")

        prompt = ENRICH_PROMPT.format(
            title=title,
            industry=rep.get("industry", "互联网"),
            company_size=rep.get("company_size", ""),
            experience_required=rep.get("experience_required", ""),
            education_required=rep.get("education_required", ""),
            description=desc,
            requirements=json.dumps(rep.get("requirements", []), ensure_ascii=False),
        )

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的 JSON 数据生成助手。请严格按照用户要求的 JSON 格式输出，不要添加任何额外文字或 markdown 标记。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        # Validate result has expected fields
        new_desc = result.get("description", desc)
        must_have = result.get("must_have_skills", [])
        nice_to_have = result.get("nice_to_have_skills", [])
        seniority = result.get("seniority_level", "mid")
        category = result.get("job_category", "")

        print(f"  description: {len(new_desc)} chars")
        print(f"  must_have: {len(must_have)} items, nice_to_have: {len(nice_to_have)} items")
        print(f"  seniority: {seniority}, category: {category}")

        # Apply to all jobs sharing this combo
        for idx in indices:
            jobs[idx]["description"] = new_desc
            jobs[idx]["must_have_skills"] = must_have
            jobs[idx]["nice_to_have_skills"] = nice_to_have
            jobs[idx]["seniority_level"] = seniority
            jobs[idx]["job_category"] = category

        enriched_count += 1
        time.sleep(0.5)  # Rate limiting

    # Write back
    data["version"] = "2.0"
    data["enriched_at"] = "2026-03-31"
    with open(MOCK_JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Enriched {enriched_count}/{len(combos)} combos, updated {len(jobs)} jobs.")


if __name__ == "__main__":
    enrich_jobs()
