"""测试共享 fixtures"""

import pytest

from resume_matcher.core.models import (
    Education,
    JobPosting,
    MatchResult,
    Platform,
    Resume,
    SalaryRange,
    WorkExperience,
)


@pytest.fixture
def sample_resume_text() -> str:
    return """张三
电话：13800138000
邮箱：zhangsan@email.com
地点：北京

教育经历：
北京大学 计算机科学与技术 本科 2015-09 至 2019-06

工作经历：
字节跳动 高级Python开发工程师 2021-03 至今
- 负责推荐系统后端开发，日处理请求量超过1亿
- 使用Python/FastAPI开发微服务，优化接口响应时间50%

美团 Python开发工程师 2019-07 至 2021-02
- 参与外卖平台订单系统开发
- 使用Django + MySQL + Redis技术栈

技能：Python, FastAPI, Django, MySQL, Redis, MongoDB, Docker, Kubernetes, Git
"""


@pytest.fixture
def sample_resume() -> Resume:
    return Resume(
        name="张三",
        phone="13800138000",
        email="zhangsan@email.com",
        location="北京",
        education=[
            Education(
                school="北京大学",
                degree="本科",
                major="计算机科学与技术",
                start_date="2015-09",
                end_date="2019-06",
            )
        ],
        work_experience=[
            WorkExperience(
                company="字节跳动",
                title="高级Python开发工程师",
                start_date="2021-03",
                end_date="至今",
                description="负责推荐系统后端开发",
                highlights=["日处理请求量超过1亿", "优化接口响应时间50%"],
            ),
            WorkExperience(
                company="美团",
                title="Python开发工程师",
                start_date="2019-07",
                end_date="2021-02",
                description="参与外卖平台订单系统开发",
            ),
        ],
        skills=["Python", "FastAPI", "Django", "MySQL", "Redis", "MongoDB", "Docker", "Kubernetes", "Git"],
    )


@pytest.fixture
def sample_jobs() -> list[JobPosting]:
    return [
        JobPosting(
            id="boss-001",
            title="Python后端开发工程师",
            company="阿里巴巴",
            location="杭州-西湖区",
            salary=SalaryRange(min_k=30, max_k=50),
            experience_required="3-5年",
            education_required="本科及以上",
            description="负责电商平台核心系统开发",
            requirements=["精通Python", "熟悉MySQL/Redis", "有分布式系统经验"],
            platform=Platform.BOSS,
        ),
        JobPosting(
            id="zhilian-001",
            title="Java开发工程师",
            company="腾讯",
            location="深圳-南山区",
            salary=SalaryRange(min_k=25, max_k=45),
            experience_required="3-5年",
            education_required="本科及以上",
            description="负责微信支付后端系统开发",
            requirements=["精通Java", "熟悉Spring框架", "了解分布式系统"],
            platform=Platform.ZHILIAN,
        ),
    ]
