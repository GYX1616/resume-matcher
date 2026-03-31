from __future__ import annotations

"""核心数据模型"""

from enum import Enum

from pydantic import BaseModel, Field


# ── 简历相关模型 ──


class Education(BaseModel):
    """教育经历"""

    school: str = ""
    degree: str = ""  # 本科, 硕士, 博士 等
    major: str = ""
    start_date: str = ""  # "YYYY-MM" 格式
    end_date: str = ""


class WorkExperience(BaseModel):
    """工作经历"""

    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    highlights: list[str] = []


class ProjectExperience(BaseModel):
    """项目经历"""

    name: str = ""
    role: str = ""
    description: str = ""
    tech_stack: list[str] = []


class Resume(BaseModel):
    """结构化简历数据"""

    name: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    summary: str = ""
    education: list[Education] = []
    work_experience: list[WorkExperience] = []
    projects: list[ProjectExperience] = []
    skills: list[str] = []
    certifications: list[str] = []
    languages: list[str] = []
    seniority_level: str = ""  # junior/mid/senior/lead
    job_category: str = ""  # 适合的岗位大类
    industry_domains: list[str] = []  # 从业行业列表
    raw_text: str = Field("", exclude=True)


# ── 岗位相关模型 ──


class Platform(str, Enum):
    """招聘平台"""

    BOSS = "boss"
    ZHILIAN = "zhilian"
    LIEPIN = "liepin"
    LAGOU = "lagou"
    JOB51 = "job51"


class SalaryRange(BaseModel):
    """薪资范围（单位：千/月）"""

    min_k: int = 0
    max_k: int = 0


class JobPosting(BaseModel):
    """岗位信息"""

    id: str
    title: str
    company: str
    company_size: str = ""
    industry: str = ""
    location: str
    salary: SalaryRange = SalaryRange()
    experience_required: str = ""
    education_required: str = ""
    description: str = ""
    requirements: list[str] = []
    must_have_skills: list[str] = []
    nice_to_have_skills: list[str] = []
    seniority_level: str = ""  # junior/mid/senior/lead
    job_category: str = ""  # backend/frontend/data/ai/pm/...
    tags: list[str] = []
    platform: Platform
    url: str = ""


# ── 匹配结果模型 ──


class MatchResult(BaseModel):
    """单条岗位匹配结果"""

    job: JobPosting
    score: float = Field(ge=0, le=100)
    match_reasons: list[str] = []
    skill_overlap: list[str] = []
    gaps: list[str] = []


# ── 搜索条件模型 ──


class SearchCriteria(BaseModel):
    """用户直接输入的搜索条件"""

    job_title: str = ""
    keywords: list[str] = []
    location: str = ""
    min_salary: int | None = None
    experience_years: int | None = None
    education: str = ""
