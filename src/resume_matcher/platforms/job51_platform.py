from __future__ import annotations

"""前程无忧 (51job) - Playwright 浏览器自动化数据采集"""

import json
import logging
import re
from typing import Optional
from urllib.parse import quote

from resume_matcher.core.models import JobPosting, Platform, SalaryRange, SearchCriteria
from resume_matcher.platforms.browser_base import (
    create_browser_context,
    random_delay,
    save_cookies,
    wait_for_login,
)

logger = logging.getLogger(__name__)

# 前程无忧 API 路径模式
SEARCH_API = "/api/job/search-pc"


def _parse_salary(salary_desc: str) -> SalaryRange:
    """解析薪资描述

    格式:
        - '0.8-1.6万/月' -> SalaryRange(8, 16)
        - '15-25万/年'   -> SalaryRange(12, 21)
        - '8-15千/月'    -> SalaryRange(8, 15)
    """
    # X-Y万/月
    match = re.search(r"([\d.]+)-([\d.]+)万/月", salary_desc)
    if match:
        return SalaryRange(
            min_k=round(float(match.group(1)) * 10),
            max_k=round(float(match.group(2)) * 10),
        )

    # X-Y千/月
    match = re.search(r"([\d.]+)-([\d.]+)千/月", salary_desc)
    if match:
        return SalaryRange(
            min_k=round(float(match.group(1))),
            max_k=round(float(match.group(2))),
        )

    # X-Y万/年
    match = re.search(r"([\d.]+)-([\d.]+)万/年", salary_desc)
    if match:
        min_annual = float(match.group(1))
        max_annual = float(match.group(2))
        return SalaryRange(
            min_k=round(min_annual * 10 / 12),
            max_k=round(max_annual * 10 / 12),
        )

    return SalaryRange()


def _build_search_url(criteria: SearchCriteria) -> str:
    """构建前程无忧搜索 URL"""
    base = "https://we.51job.com/pc/search"
    params = []
    if criteria.job_title:
        params.append(f"keyword={quote(criteria.job_title)}")
    if criteria.location:
        params.append(f"searchType=2&keywordType=0&jobArea={quote(criteria.location)}")
    if params:
        return f"{base}?{'&'.join(params)}"
    return base


def _parse_search_response(data: dict) -> list[JobPosting]:
    """解析前程无忧搜索 API 响应"""
    jobs = []

    # 前程无忧 API 响应结构
    result_list = data.get("resultbody", {}).get("job", {}).get("items", [])

    for item in result_list:
        try:
            job_id = str(item.get("jobId", ""))
            title = item.get("jobName", "")
            company = item.get("companyName", "")
            location = item.get("jobAreaString", "")
            salary_text = item.get("provideSalaryString", "")
            experience = item.get("jobWorkyear", "")
            education = item.get("jobDegreeString", "")
            tags = item.get("jobTags", [])
            if isinstance(tags, list):
                tags = [t if isinstance(t, str) else str(t) for t in tags]
            company_size = item.get("companySize", "")
            industry = item.get("companyIndustry", "")
            description = item.get("jobDescribe", "")

            job = JobPosting(
                id=f"job51_{job_id}",
                title=title,
                company=company,
                company_size=company_size,
                industry=industry,
                location=location,
                salary=_parse_salary(salary_text),
                experience_required=experience,
                education_required=education,
                description=description,
                requirements=[],
                tags=tags,
                platform=Platform.JOB51,
                url=f"https://we.51job.com/pc/search/jobDetail?jobId={job_id}",
            )
            jobs.append(job)
        except Exception as e:
            logger.warning("解析前程无忧岗位失败: %s", e)
            continue

    return jobs


class Job51Platform:
    """前程无忧 - 通过 Playwright 拦截 API 响应获取真实数据"""

    platform = Platform.JOB51

    def __init__(self, headless: bool = False):
        self.headless = headless

    def search(self, criteria: SearchCriteria) -> list[JobPosting]:
        """搜索岗位"""
        from playwright.sync_api import sync_playwright

        all_jobs: list[JobPosting] = []

        with sync_playwright() as pw:
            browser, context, page = create_browser_context(
                pw, "job51", headless=self.headless
            )

            try:
                search_url = _build_search_url(criteria)
                page.goto(search_url, wait_until="domcontentloaded")
                random_delay(2, 4)

                # 检查登录状态
                if "login" in page.url.lower() or "passport" in page.url.lower():
                    logged_in = wait_for_login(
                        page,
                        check_selector=".joblist, .j_joblist, [class*='job-list']",
                        platform="前程无忧",
                    )
                    if not logged_in:
                        logger.error("前程无忧登录失败")
                        return []
                    page.goto(search_url, wait_until="domcontentloaded")
                    random_delay(2, 4)

                # 拦截 API 响应
                captured_responses: list[dict] = []

                def handle_response(response):
                    if SEARCH_API in response.url:
                        try:
                            data = response.json()
                            captured_responses.append(data)
                        except Exception:
                            pass

                page.on("response", handle_response)

                # 翻页采集
                for page_num in range(3):
                    if page_num > 0:
                        next_btn = page.query_selector(
                            ".pagination .next, [class*='next'], button:has-text('下一页')"
                        )
                        if next_btn and next_btn.is_visible():
                            next_btn.click()
                            random_delay(2, 4)
                        else:
                            break

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    random_delay(1, 2)

                # 解析拦截到的响应
                for resp_data in captured_responses:
                    jobs = _parse_search_response(resp_data)
                    all_jobs.extend(jobs)

                # 备选：DOM 解析
                if not all_jobs:
                    all_jobs = self._parse_from_dom(page)

                save_cookies(page, "job51")
                logger.info("前程无忧获取到 %d 个岗位", len(all_jobs))

            except Exception as e:
                logger.error("前程无忧数据采集失败: %s", e)
            finally:
                browser.close()

        return all_jobs

    def _parse_from_dom(self, page) -> list[JobPosting]:
        """从 DOM 提取岗位信息"""
        jobs = []
        try:
            cards = page.query_selector_all(
                ".joblist-item, .j_joblist .e, [class*='JobCard'], [class*='job-card']"
            )
            for card in cards:
                try:
                    title_el = card.query_selector(
                        ".jname, .job-name, [class*='title']"
                    )
                    company_el = card.query_selector(
                        ".cname, .company-name, [class*='company']"
                    )
                    salary_el = card.query_selector(
                        ".sal, .salary, [class*='salary']"
                    )
                    location_el = card.query_selector(
                        ".info .d, [class*='area'], [class*='location']"
                    )
                    link_el = card.query_selector("a[href*='job']")

                    title = title_el.inner_text().strip() if title_el else ""
                    company = company_el.inner_text().strip() if company_el else ""
                    salary_text = salary_el.inner_text().strip() if salary_el else ""
                    location = location_el.inner_text().strip() if location_el else ""
                    href = link_el.get_attribute("href") if link_el else ""

                    job = JobPosting(
                        id=f"job51_dom_{id(card)}",
                        title=title,
                        company=company,
                        location=location,
                        salary=_parse_salary(salary_text),
                        platform=Platform.JOB51,
                        url=href if href.startswith("http") else f"https://we.51job.com{href}",
                    )
                    if title:
                        jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            logger.warning("前程无忧 DOM 解析失败: %s", e)

        return jobs
