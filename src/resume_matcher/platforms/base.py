from __future__ import annotations

"""岗位平台基类"""

from typing import Protocol

from resume_matcher.core.models import JobPosting, Platform, SearchCriteria


class JobPlatform(Protocol):
    """招聘平台协议 - 所有平台适配器需实现此接口"""

    platform: Platform

    def search(self, criteria: SearchCriteria) -> list[JobPosting]:
        """根据搜索条件返回岗位列表"""
        ...
