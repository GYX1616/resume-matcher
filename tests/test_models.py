"""数据模型测试"""

from resume_matcher.core.models import (
    Education,
    JobPosting,
    MatchResult,
    Platform,
    Resume,
    SalaryRange,
    SearchCriteria,
    WorkExperience,
)


def test_resume_creation():
    resume = Resume(name="张三", skills=["Python", "Java"])
    assert resume.name == "张三"
    assert len(resume.skills) == 2
    assert resume.education == []


def test_resume_with_education():
    edu = Education(school="北京大学", degree="本科", major="计算机科学")
    resume = Resume(name="李四", education=[edu])
    assert resume.education[0].school == "北京大学"


def test_job_posting_creation():
    job = JobPosting(
        id="test-001",
        title="Python工程师",
        company="测试公司",
        location="北京",
        platform=Platform.BOSS,
    )
    assert job.id == "test-001"
    assert job.salary.min_k == 0


def test_salary_range():
    salary = SalaryRange(min_k=20, max_k=40)
    assert salary.min_k == 20
    assert salary.max_k == 40


def test_match_result():
    job = JobPosting(
        id="test-001",
        title="Python工程师",
        company="测试公司",
        location="北京",
        platform=Platform.BOSS,
    )
    result = MatchResult(
        job=job,
        score=85.5,
        match_reasons=["技能匹配度高"],
        skill_overlap=["Python"],
        gaps=["缺少Go经验"],
    )
    assert result.score == 85.5
    assert len(result.match_reasons) == 1


def test_search_criteria():
    criteria = SearchCriteria(
        job_title="Python开发",
        location="上海",
        keywords=["FastAPI", "微服务"],
    )
    assert criteria.job_title == "Python开发"
    assert len(criteria.keywords) == 2


def test_platform_enum():
    assert Platform.BOSS.value == "boss"
    assert Platform.ZHILIAN.value == "zhilian"
    assert Platform.LIEPIN.value == "liepin"
    assert Platform.LAGOU.value == "lagou"
