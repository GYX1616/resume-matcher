from __future__ import annotations

"""平台注册表 - 管理所有平台适配器"""

import logging
from typing import Any

from resume_matcher.core.models import JobPosting, Platform, SearchCriteria
from resume_matcher.platforms.mock_platform import MockPlatform

logger = logging.getLogger(__name__)


def _get_mock_platforms() -> list[Any]:
    """获取所有模拟平台"""
    return [
        MockPlatform(Platform.BOSS),
        MockPlatform(Platform.ZHILIAN),
        MockPlatform(Platform.LIEPIN),
        MockPlatform(Platform.LAGOU),
    ]


def _get_real_platforms(headless: bool = False) -> list[Any]:
    """获取所有真实平台（Playwright 浏览器自动化）"""
    from resume_matcher.platforms.boss_platform import BossPlatform
    from resume_matcher.platforms.job51_platform import Job51Platform
    from resume_matcher.platforms.liepin_platform import LiepinPlatform

    return [
        BossPlatform(headless=headless),
        LiepinPlatform(headless=headless),
        Job51Platform(headless=headless),
    ]


def get_all_jobs(
    criteria: SearchCriteria,
    platform_filter: str | None = None,
    use_real: bool = False,
    headless: bool = False,
) -> list[JobPosting]:
    """从所有平台（或指定平台）获取岗位列表

    Args:
        criteria: 搜索条件
        platform_filter: 平台筛选（如 "boss", "liepin", "job51"）
        use_real: 是否使用真实平台（Playwright 浏览器自动化）
        headless: 浏览器是否无头模式（首次登录需设为 False）

    Returns:
        岗位列表
    """
    if use_real:
        platforms = _get_real_platforms(headless=headless)
    else:
        platforms = _get_mock_platforms()

    if platform_filter:
        platforms = [p for p in platforms if p.platform.value == platform_filter]

    all_jobs: list[JobPosting] = []
    for platform in platforms:
        try:
            jobs = platform.search(criteria)
            all_jobs.extend(jobs)
            logger.info("从 %s 获取到 %d 个岗位", platform.platform.value, len(jobs))
        except Exception as e:
            logger.error("从 %s 获取岗位失败: %s", platform.platform.value, e)

    return all_jobs
