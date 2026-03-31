from __future__ import annotations

"""猎聘 - Playwright 浏览器自动化数据采集"""

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

# 猎聘 API 路径模式
SEARCH_API = "com.liepin.searchfront4c.pc-search-job"


def _parse_salary(salary_desc: str) -> SalaryRange:
    """解析薪资描述，如 '15-25k' 或 '15-25万/年'"""
    # 月薪：15-25k
    match = re.search(r"(\d+)-(\d+)[kK]", salary_desc)
    if match:
        return SalaryRange(min_k=int(match.group(1)), max_k=int(match.group(2)))

    # 年薪：15-25万
    match = re.search(r"(\d+)-(\d+)万", salary_desc)
    if match:
        # 年薪转月薪（除以12），单位K
        min_annual = int(match.group(1))
        max_annual = int(match.group(2))
        return SalaryRange(
            min_k=round(min_annual * 10 / 12),
            max_k=round(max_annual * 10 / 12),
        )

    return SalaryRange()


def _build_search_url(criteria: SearchCriteria) -> str:
    """构建猎聘搜索 URL"""
    base = "https://www.liepin.com/zhaopin/"
    params = []
    if criteria.job_title:
        params.append(f"key={quote(criteria.job_title)}")
    if criteria.location:
        params.append(f"dq={quote(criteria.location)}")
    if params:
        return f"{base}?{'&'.join(params)}"
    return base


def _parse_search_response(data: dict) -> list[JobPosting]:
    """解析猎聘搜索 API 响应"""
    jobs = []

    # 猎聘 API 响应结构
    job_list = (
        data.get("data", {})
        .get("data", {})
        .get("jobCardList", [])
    )

    for item in job_list:
        try:
            job_data = item.get("job", {})
            company_data = item.get("comp", {})

            job_id = str(job_data.get("jobId", ""))
            title = job_data.get("title", "")
            company = company_data.get("compName", "")
            location = job_data.get("dq", "")
            salary_text = job_data.get("salary", "")
            experience = job_data.get("requireWorkYears", "")
            education = job_data.get("requireEduLevel", "")
            tags = job_data.get("labels", {}).get("jobLabels", [])
            if isinstance(tags, list):
                tags = [t.get("label", t) if isinstance(t, dict) else str(t) for t in tags]
            company_size = company_data.get("compScale", "")
            industry = company_data.get("compIndustry", "")

            job = JobPosting(
                id=f"liepin_{job_id}",
                title=title,
                company=company,
                company_size=company_size,
                industry=industry,
                location=location,
                salary=_parse_salary(salary_text),
                experience_required=experience,
                education_required=education,
                description=job_data.get("jobDesc", ""),
                requirements=[],
                tags=tags,
                platform=Platform.LIEPIN,
                url=f"https://www.liepin.com/job/{job_id}.shtml",
            )
            jobs.append(job)
        except Exception as e:
            logger.warning("解析猎聘岗位失败: %s", e)
            continue

    return jobs


class LiepinPlatform:
    """猎聘 - 通过 Playwright 拦截 API 响应获取真实数据"""

    platform = Platform.LIEPIN

    def __init__(self, headless: bool = False):
        self.headless = headless

    def search(self, criteria: SearchCriteria) -> list[JobPosting]:
        """搜索岗位"""
        from playwright.sync_api import sync_playwright

        all_jobs: list[JobPosting] = []

        with sync_playwright() as pw:
            browser, context, page = create_browser_context(
                pw, "liepin", headless=self.headless
            )

            try:
                search_url = _build_search_url(criteria)
                page.goto(search_url, wait_until="domcontentloaded")
                random_delay(2, 4)

                # 检查登录状态
                if "passport" in page.url.lower() or "login" in page.url.lower():
                    logged_in = wait_for_login(
                        page,
                        check_selector=".job-list-box, .content-left-section",
                        platform="猎聘",
                    )
                    if not logged_in:
                        logger.error("猎聘登录失败")
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
                        # 点击下一页
                        next_btn = page.query_selector(
                            ".pagination .next, [class*='next']"
                        )
                        if next_btn and next_btn.is_visible():
                            next_btn.click()
                            random_delay(2, 4)
                        else:
                            break

                    # 滚动触发懒加载
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    random_delay(1, 2)

                # 解析拦截到的响应
                for resp_data in captured_responses:
                    jobs = _parse_search_response(resp_data)
                    all_jobs.extend(jobs)

                # 备选：DOM 解析
                if not all_jobs:
                    all_jobs = self._parse_from_dom(page)

                save_cookies(page, "liepin")
                logger.info("猎聘获取到 %d 个岗位", len(all_jobs))

            except Exception as e:
                logger.error("猎聘数据采集失败: %s", e)
            finally:
                browser.close()

        return all_jobs

    def _parse_from_dom(self, page) -> list[JobPosting]:
        """从 DOM 提取岗位信息"""
        jobs = []
        try:
            cards = page.query_selector_all(
                ".job-card, .job-card-pc-container, [class*='JobCard']"
            )
            for card in cards:
                try:
                    title_el = card.query_selector(
                        ".job-title, .ellipsis-1, [class*='title']"
                    )
                    company_el = card.query_selector(
                        ".company-name, [class*='company']"
                    )
                    salary_el = card.query_selector(
                        ".job-salary, [class*='salary']"
                    )
                    location_el = card.query_selector(
                        ".job-dq, [class*='city'], [class*='location']"
                    )
                    link_el = card.query_selector("a[href*='job']")

                    title = title_el.inner_text().strip() if title_el else ""
                    company = company_el.inner_text().strip() if company_el else ""
                    salary_text = salary_el.inner_text().strip() if salary_el else ""
                    location = location_el.inner_text().strip() if location_el else ""
                    href = link_el.get_attribute("href") if link_el else ""

                    job_id_match = re.search(r"/job/(\d+)", href or "")
                    job_id = job_id_match.group(1) if job_id_match else str(id(card))

                    job = JobPosting(
                        id=f"liepin_{job_id}",
                        title=title,
                        company=company,
                        location=location,
                        salary=_parse_salary(salary_text),
                        platform=Platform.LIEPIN,
                        url=href if href.startswith("http") else f"https://www.liepin.com{href}",
                    )
                    if title:
                        jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            logger.warning("猎聘 DOM 解析失败: %s", e)

        return jobs
