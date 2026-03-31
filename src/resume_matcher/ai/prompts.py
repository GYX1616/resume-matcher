from __future__ import annotations

"""AI Prompt 模板"""

RESUME_PARSE_PROMPT = """你是一个资深的猎头顾问和简历分析专家。请仔细阅读以下简历，提取结构化信息，并深入分析候选人的核心竞争力。

## 分析要求

1. **基本信息提取**：姓名、联系方式、所在地等
2. **教育背景**：学校、学历、专业、时间
3. **工作经历**：公司、职位、时间、职责描述、核心亮点成果
4. **项目经验**：项目名称、角色、项目描述、技术栈，以及该项目的核心亮点和业务价值
5. **技能提取**：将简历中提到的所有技能拆分为独立项（包括工具、技术、方法论、行业知识等）
6. **候选人画像摘要（summary）**：用 4-6 句话深入总结此人的：
   - 职业轨迹和发展方向
   - 核心技术深度和广度
   - 行业经验和领域专长
   - 最突出的成就和差异化优势
   - 最适合的岗位方向和职级
   这是最重要的字段，必须深入分析而非简单复述。
7. **资历等级（seniority_level）**：根据工作年限、职位层级、管理经验判断：
   - "junior"（初级，0-2年经验，执行层）
   - "mid"（中级，2-5年经验，独立负责）
   - "senior"（高级，5-10年经验，核心骨干）
   - "lead"（负责人，8年以上，带团队或主导技术方向）
8. **适合岗位类别（job_category）**：判断此人最适合的岗位大类：
   backend / frontend / fullstack / data / ai / devops / test / security / pm / design
9. **从业行业（industry_domains）**：提取候选人从业过的行业领域列表（如：金融、电商、AI、教育、医疗等）

## 特别注意

- 从项目和工作描述中提炼出**量化成果**（如提升XX%、节省XX万、服务XX用户）
- 识别候选人的**行业经验**和**领域知识**（如金融、电商、AI、教育等）
- 在 highlights 中总结每段经历的**核心贡献和成果**，而非简单复述职责
- 日期格式统一为 "YYYY-MM"，如无法确定具体月份可写 "YYYY"
- 如果某个字段无法从简历中提取，设为空字符串或空列表

## 简历内容

---
{resume_text}
---

请以 JSON 格式输出。"""


JOB_MATCH_PROMPT = """你是一个资深的职业发展顾问和招聘匹配专家。请根据候选人的详细背景与每个岗位的 JD，进行深度匹配分析。

## 候选人画像

**姓名**：{name}
**职业定位**：{summary}
**资历等级**：{seniority_level}
**岗位类别**：{job_category}
**行业经验**：{industry_domains}
**核心技能**：{skills}
**工作经历**：
{experience_summary}
**教育背景**：{education_summary}
**项目亮点**：
{project_highlights}
**期望职位**：{target_title}
**期望地点**：{target_location}

## 待匹配岗位列表

{jobs_json}

## 匹配分析要求

请逐个阅读每个岗位的 description（职位描述）、must_have_skills（必须技能）和 nice_to_have_skills（加分技能），与候选人的背景进行深度对比。

### 硬性过滤规则（先判断，再评分）：
- 如果候选人的 **岗位类别** 与目标岗位完全不同（如前端开发去匹配后端岗位），分数上限为 50
- 如果候选人的 **资历等级** 与岗位差距超过 1 级（如 junior 匹配 senior 岗位），分数上限为 40
- 如果候选人 **期望地点** 与岗位地点不同且候选人明确指定了地点，扣 10 分

### 评分维度（总分 100）：
1. **必须技能覆盖率（30%）**：候选人满足了多少 must_have_skills？每项必须技能的匹配程度如何？
2. **经验相关度（25%）**：工作年限、行业经验、过往职责与岗位的相关性
3. **项目深度（20%）**：候选人过往项目的业务场景、技术方案、成果与岗位职责的关联度
4. **加分项匹配（15%）**：nice_to_have_skills 的覆盖情况
5. **成长适配（10%）**：候选人的职业轨迹是否符合该岗位的职级和发展方向

### 评分校准指南：
- **90-100**：几乎完美匹配 - 技能、经验、行业高度吻合，资历等级匹配
- **70-89**：强匹配 - 核心必须技能满足，经验相关，有少量 gap
- **50-69**：中等匹配 - 部分技能和经验相关，但有明显 gap
- **30-49**：弱匹配 - 仅有少量技能重合，岗位方向有偏差
- **0-29**：基本不匹配 - 技能、经验、方向都不吻合

### 输出要求

对每个岗位输出：
- **job_id**: 岗位 ID（必须与输入一致）
- **score**: 0-100 的综合匹配分数（遵循上述校准指南）
- **match_reasons**: 2-3 条具体的匹配原因（说明为什么候选人适合，引用具体的技能/经验/项目）
- **skill_overlap**: 候选人具备的与岗位相关的技能列表
- **gaps**: 岗位要求但候选人缺少的能力或经验

**重要**：即使匹配度不高也必须给出评分，不要跳过任何岗位。每个岗位都必须出现在 results 中。

请以 JSON 格式输出。"""


def build_resume_parse_prompt(resume_text: str) -> str:
    return RESUME_PARSE_PROMPT.format(resume_text=resume_text)


def build_job_match_prompt(
    name: str,
    summary: str,
    skills: list[str],
    experience_summary: str,
    education_summary: str,
    project_highlights: str,
    seniority_level: str,
    job_category: str,
    industry_domains: list[str],
    target_title: str,
    target_location: str,
    jobs_json: str,
) -> str:
    return JOB_MATCH_PROMPT.format(
        name=name,
        summary=summary or "未提供",
        skills=", ".join(skills) if skills else "未提供",
        experience_summary=experience_summary or "未提供",
        education_summary=education_summary or "未提供",
        project_highlights=project_highlights or "未提供",
        seniority_level=seniority_level or "未判断",
        job_category=job_category or "未判断",
        industry_domains=", ".join(industry_domains) if industry_domains else "未提供",
        target_title=target_title or "未指定",
        target_location=target_location or "不限",
        jobs_json=jobs_json,
    )
