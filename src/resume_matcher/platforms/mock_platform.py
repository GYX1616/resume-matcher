from __future__ import annotations

"""统一的模拟平台适配器"""

import json
from importlib import resources
from functools import lru_cache

from urllib.parse import quote

from resume_matcher.core.models import JobPosting, Platform, SearchCriteria

# 各平台的搜索页 URL 模板（用岗位名称搜索）
_PLATFORM_SEARCH_URLS = {
    Platform.BOSS: "https://www.zhipin.com/web/geek/job?query={query}&city=100010000",
    Platform.ZHILIAN: "https://sou.zhaopin.com/?jl=530&kw={query}",
    Platform.LIEPIN: "https://www.liepin.com/zhaopin/?key={query}",
    Platform.LAGOU: "https://www.lagou.com/wn/zhaopin?kd={query}",
    Platform.JOB51: "https://we.51job.com/pc/search?keyword={query}",
}


def _generate_search_url(platform: Platform, job_title: str) -> str:
    """为 mock 岗位生成平台搜索页链接"""
    template = _PLATFORM_SEARCH_URLS.get(platform, "")
    if not template:
        return ""
    return template.format(query=quote(job_title))


@lru_cache(maxsize=1)
def _load_mock_data() -> list[dict]:
    """加载模拟岗位数据"""
    data_path = resources.files("resume_matcher.data").joinpath("mock_jobs.json")
    with resources.as_file(data_path) as f:
        data = json.loads(f.read_text(encoding="utf-8"))
    return data["jobs"]


class MockPlatform:
    """模拟招聘平台 - 从 mock_jobs.json 加载数据"""

    def __init__(self, platform: Platform):
        self.platform = platform

    def search(self, criteria: SearchCriteria) -> list[JobPosting]:
        """根据搜索条件筛选岗位

        筛选策略：宽松匹配，尽量多返回岗位，让 AI 来做精确匹配。
        - 没有搜索条件时返回该平台所有岗位
        - 有条件时使用 OR 逻辑（标题/描述/关键词任一匹配即可）
        - 地点仅作为加分项，不作为硬性过滤
        """
        all_jobs = _load_mock_data()

        # 筛选当前平台的岗位
        platform_jobs = [j for j in all_jobs if j["platform"] == self.platform.value]

        # 没有任何搜索条件，返回该平台全部岗位
        has_criteria = criteria.job_title or criteria.keywords or criteria.location
        if not has_criteria:
            return [self._with_url(JobPosting.model_validate(j)) for j in platform_jobs]

        results = []
        for job_data in platform_jobs:
            job = JobPosting.model_validate(job_data)
            job_text = f"{job.title} {job.description} {' '.join(job.requirements)}".lower()

            matched = False

            # 标题/描述匹配
            if criteria.job_title:
                if criteria.job_title.lower() in job_text:
                    matched = True

            # 关键词匹配（任一关键词命中即可）
            if criteria.keywords:
                if any(kw.lower() in job_text for kw in criteria.keywords):
                    matched = True

            # 地点匹配
            if criteria.location:
                if criteria.location in job.location:
                    matched = True

            if matched:
                results.append(self._with_url(job))

        return results

    def _with_url(self, job: JobPosting) -> JobPosting:
        """为没有 URL 的 mock 岗位生成平台搜索链接"""
        if not job.url:
            job.url = _generate_search_url(self.platform, job.title)
        return job
