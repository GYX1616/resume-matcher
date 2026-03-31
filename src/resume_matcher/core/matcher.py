from __future__ import annotations

"""匹配引擎 - 简历与岗位的智能匹配"""

import json
import logging

from resume_matcher.ai.client import create_client, generate_structured

logger = logging.getLogger(__name__)
from resume_matcher.ai.prompts import build_job_match_prompt
from resume_matcher.ai.schemas import MATCH_SCHEMA
from resume_matcher.core.models import (
    JobPosting,
    MatchResult,
    Resume,
    SearchCriteria,
)

BATCH_SIZE = 5  # 每批处理的岗位数量


def _summarize_experience(resume: Resume) -> str:
    """生成工作经验摘要（含核心亮点）"""
    if not resume.work_experience:
        return "无工作经验"
    parts = []
    for exp in resume.work_experience:
        period = f"{exp.start_date}-{exp.end_date}" if exp.start_date else ""
        line = f"{exp.company} {exp.title} {period}"
        if exp.description:
            line += f"\n  职责: {exp.description}"
        if exp.highlights:
            line += f"\n  亮点: {'; '.join(exp.highlights)}"
        parts.append(line)
    return "\n".join(parts)


def _summarize_education(resume: Resume) -> str:
    """生成教育背景摘要"""
    if not resume.education:
        return "未提供"
    parts = []
    for edu in resume.education:
        parts.append(f"{edu.school} {edu.degree} {edu.major}")
    return "; ".join(parts)


def _summarize_projects(resume: Resume) -> str:
    """生成项目经验摘要"""
    if not resume.projects:
        return ""
    parts = []
    for proj in resume.projects:
        line = f"- {proj.name}"
        if proj.role:
            line += f"（{proj.role}）"
        if proj.description:
            line += f": {proj.description}"
        if proj.tech_stack:
            line += f" [技术栈: {', '.join(proj.tech_stack)}]"
        parts.append(line)
    return "\n".join(parts)


def _jobs_to_json(jobs: list[JobPosting]) -> str:
    """将岗位列表转为 JSON 字符串（供 Prompt 使用），包含完整 JD"""
    items = []
    for job in jobs:
        item = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": f"{job.salary.min_k}K-{job.salary.max_k}K",
            "experience_required": job.experience_required,
            "education_required": job.education_required,
            "description": job.description,
            "must_have_skills": job.must_have_skills,
            "nice_to_have_skills": job.nice_to_have_skills,
            "seniority_level": job.seniority_level,
            "job_category": job.job_category,
        }
        # 兼容旧数据：如果没有 must_have_skills，使用 requirements
        if not item["must_have_skills"] and job.requirements:
            item["requirements"] = job.requirements
        items.append(item)
    return json.dumps(items, ensure_ascii=False, indent=2)


def match_jobs(
    resume: Resume,
    jobs: list[JobPosting],
    criteria: SearchCriteria,
    model_name: str = "deepseek-chat",
    api_key: str = "",
    base_url: str = "https://api.deepseek.com",
) -> list[MatchResult]:
    """将简历与岗位列表进行匹配，返回按分数排序的结果

    采用批量处理策略，每次发送 BATCH_SIZE 个岗位给 AI 评分。
    """
    if not jobs:
        return []

    client = create_client(api_key=api_key, base_url=base_url)
    all_results: list[MatchResult] = []
    job_map = {job.id: job for job in jobs}

    # 分批处理
    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        jobs_json = _jobs_to_json(batch)

        prompt = build_job_match_prompt(
            name=resume.name,
            summary=resume.summary,
            skills=resume.skills,
            experience_summary=_summarize_experience(resume),
            education_summary=_summarize_education(resume),
            project_highlights=_summarize_projects(resume),
            seniority_level=resume.seniority_level,
            job_category=resume.job_category,
            industry_domains=resume.industry_domains,
            target_title=criteria.job_title,
            target_location=criteria.location,
            jobs_json=jobs_json,
        )

        try:
            data = generate_structured(
                client=client,
                model=model_name,
                prompt=prompt,
                json_schema=MATCH_SCHEMA,
                temperature=0.3,
            )
        except Exception as e:
            logger.warning("Batch %d-%d matching failed: %s", i, i + len(batch), e)
            continue

        for item in data.get("results", []):
            job_id = item.get("job_id", "")
            job = job_map.get(job_id)
            if not job:
                continue

            score = min(max(float(item.get("score", 0)), 0), 100)
            result = MatchResult(
                job=job,
                score=score,
                match_reasons=item.get("match_reasons", []),
                skill_overlap=item.get("skill_overlap", []),
                gaps=item.get("gaps", []),
            )
            all_results.append(result)

    # 按分数降序排序
    all_results.sort(key=lambda r: r.score, reverse=True)
    return all_results
