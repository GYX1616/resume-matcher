from __future__ import annotations

"""Boss直聘 - Playwright 浏览器自动化数据采集"""

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

# Boss直聘 API 路径模式
JOB_LIST_API = "/wapi/zpgeek/search/joblist.json"
JOB_DETAIL_API = "/wapi/zpgeek/job/detail.json"


def _parse_salary(salary_desc: str) -> SalaryRange:
    """解析薪资描述，如 '15-25K·14薪' -> SalaryRange(15, 25)"""
    match = re.search(r"(\d+)-(\d+)[Kk]", salary_desc)
    if match:
        return SalaryRange(min_k=int(match.group(1)), max_k=int(match.group(2)))
    return SalaryRange()


def _build_search_url(criteria: SearchCriteria) -> str:
    """构建 Boss直聘搜索 URL"""
    base = "https://www.zhipin.com/web/geek/job"
    params = []
    if criteria.job_title:
        params.append(f"query={quote(criteria.job_title)}")
    if criteria.location:
        params.append(f"city={quote(criteria.location)}")
    if params:
        return f"{base}?{'&'.join(params)}"
    return base


def _parse_job_list_response(data: dict) -> list[JobPosting]:
    """解析 Boss直聘 搜索列表 API 响应"""
    jobs = []
    job_list = data.get("zpData", {}).get("jobList", [])

    for item in job_list:
        try:
            job_id = str(item.get("encryptJobId", ""))
            title = item.get("jobName", "")
            company = item.get("brandName", "")
            location = item.get("cityName", "")
            area = item.get("areaDistrict", "")
            if area:
                location = f"{location} {area}"

            salary = _parse_salary(item.get("salaryDesc", ""))
            experience = item.get("jobExperience", "")
            education = item.get("jobDegree", "")
            tags = item.get("skills", [])
            company_size = item.get("brandScaleName", "")
            industry = item.get("brandIndustry", "")

            job = JobPosting(
                id=f"boss_{job_id}",
                title=title,
                company=company,
                company_size=company_size,
                industry=industry,
                location=location,
                salary=salary,
                experience_required=experience,
                education_required=education,
                description="",  # 列表页无详情，需单独获取
                requirements=[],
                tags=tags,
                platform=Platform.BOSS,
                url=f"https://www.zhipin.com/job_detail/{job_id}.html",
            )
            jobs.append(job)
        except Exception as e:
            logger.warning("解析 Boss 岗位失败: %s", e)
            continue

    return jobs


class BossPlatform:
    """Boss直聘 - 通过 Playwright 拦截 API 响应获取真实数据"""

    platform = Platform.BOSS

    def __init__(self, headless: bool = False):
        self.headless = headless

    def search(self, criteria: SearchCriteria) -> list[JobPosting]:
        """搜索岗位，通过浏览器自动化拦截 API 响应"""
        from playwright.sync_api import sync_playwright

        all_jobs: list[JobPosting] = []

        with sync_playwright() as pw:
            browser, context, page = create_browser_context(
                pw, "boss", headless=self.headless
            )

            try:
                # 访问搜索页
                search_url = _build_search_url(criteria)
                page.goto(search_url, wait_until="domcontentloaded")
                random_delay(2, 4)

                # 检查是否需要登录
                if "login" in page.url.lower():
                    logged_in = wait_for_login(
                        page,
                        check_selector=".job-list-box",
                        platform="Boss直聘",
                    )
                    if not logged_in:
                        logger.error("Boss直聘登录失败，无法获取数据")
                        return []
                    # 登录后重新访问搜索页
                    page.goto(search_url, wait_until="domcontentloaded")
                    random_delay(2, 4)

                # 设置 API 响应拦截
                captured_responses: list[dict] = []

                def handle_response(response):
                    if JOB_LIST_API in response.url:
                        try:
                            data = response.json()
                            captured_responses.append(data)
                        except Exception:
                            pass

                page.on("response", handle_response)

                # 滚动页面触发加载（Boss直聘使用无限滚动）
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    random_delay(1.5, 3)

                # 如果滚动没有触发 API，尝试点击"下一页"
                if not captured_responses:
                    # 首次加载的数据可能已在页面中，尝试刷新触发
                    page.reload(wait_until="domcontentloaded")
                    random_delay(2, 4)

                # 解析拦截到的响应
                for resp_data in captured_responses:
                    jobs = _parse_job_list_response(resp_data)
                    all_jobs.extend(jobs)

                # 如果 API 拦截没有结果，尝试从页面 DOM 提取
                if not all_jobs:
                    all_jobs = self._parse_from_dom(page)

                save_cookies(page, "boss")
                logger.info("Boss直聘获取到 %d 个岗位", len(all_jobs))

            except Exception as e:
                logger.error("Boss直聘数据采集失败: %s", e)
            finally:
                browser.close()

        return all_jobs

    def _parse_from_dom(self, page) -> list[JobPosting]:
        """从页面 DOM 直接提取岗位信息（备选方案）"""
        jobs = []
        try:
            cards = page.query_selector_all(".job-card-wrapper")
            for card in cards:
                try:
                    title_el = card.query_selector(".job-name")
                    company_el = card.query_selector(".company-name a")
                    salary_el = card.query_selector(".salary")
                    location_el = card.query_selector(".job-area")
                    link_el = card.query_selector(".job-card-left a")
                    tags_els = card.query_selector_all(".tag-list li")
                    info_els = card.query_selector_all(".job-info .tag-list li")

                    title = title_el.inner_text().strip() if title_el else ""
                    company = company_el.inner_text().strip() if company_el else ""
                    salary_text = salary_el.inner_text().strip() if salary_el else ""
                    location = location_el.inner_text().strip() if location_el else ""
                    href = link_el.get_attribute("href") if link_el else ""
                    tags = [t.inner_text().strip() for t in tags_els]

                    # 从 URL 提取 job_id
                    job_id_match = re.search(r"/job_detail/([^.]+)", href or "")
                    job_id = job_id_match.group(1) if job_id_match else f"boss_dom_{id(card)}"

                    job = JobPosting(
                        id=f"boss_{job_id}",
                        title=title,
                        company=company,
                        location=location,
                        salary=_parse_salary(salary_text),
                        tags=tags,
                        platform=Platform.BOSS,
                        url=f"https://www.zhipin.com{href}" if href else "",
                    )
                    if title:
                        jobs.append(job)
                except Exception as e:
                    logger.debug("DOM 解析单条岗位失败: %s", e)
                    continue
        except Exception as e:
            logger.warning("DOM 解析失败: %s", e)

        return jobs
