"""Streamlit Web 应用 - 智能岗位匹配"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from resume_matcher.core.config import get_settings
from resume_matcher.core.models import SearchCriteria

# ── 页面配置 ──
st.set_page_config(
    page_title="智能岗位匹配",
    page_icon="🎯",
    layout="wide",
)

# ── 自定义样式 ──
st.markdown("""
<style>
    .score-high { color: #22c55e; font-weight: bold; font-size: 1.2em; }
    .score-mid  { color: #eab308; font-weight: bold; font-size: 1.2em; }
    .score-low  { color: #ef4444; font-weight: bold; font-size: 1.2em; }
    .job-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        background: #fafafa;
    }
    .stExpander { border: none !important; }
</style>
""", unsafe_allow_html=True)


def _score_class(score: float) -> str:
    if score >= 80:
        return "score-high"
    if score >= 60:
        return "score-mid"
    return "score-low"


def _format_salary(min_k: int, max_k: int) -> str:
    if min_k and max_k:
        return f"{min_k}K-{max_k}K/月"
    if min_k:
        return f"{min_k}K+/月"
    if max_k:
        return f"~{max_k}K/月"
    return "薪资面议"


PLATFORM_NAMES = {
    "boss": "Boss直聘",
    "zhilian": "智联招聘",
    "liepin": "猎聘",
    "lagou": "拉勾",
    "job51": "前程无忧",
}


def main():
    settings = get_settings()

    # ── 标题 ──
    st.title("🎯 智能岗位匹配")
    st.caption("上传简历，AI 帮你找到最匹配的工作岗位")

    # ── 侧边栏：设置 ──
    with st.sidebar:
        st.header("⚙️ 设置")
        api_key = st.text_input("DeepSeek API Key", value=settings.deepseek_api_key, type="password")
        model_name = st.text_input("模型", value=settings.deepseek_model)
        base_url = st.text_input("API URL", value=settings.deepseek_base_url)
        top_n = st.slider("显示结果数量", min_value=1, max_value=50, value=settings.default_top_n)
        min_score = st.slider("最低匹配分数", min_value=0, max_value=100, value=0)
        platform_options = ["all", "boss", "zhilian", "liepin", "lagou", "job51"]
        platform = st.selectbox(
            "平台筛选",
            options=platform_options,
            format_func=lambda x: "全部平台" if x == "all" else PLATFORM_NAMES.get(x, x),
        )

        st.divider()
        st.header("🌐 数据来源")
        use_real = st.toggle("使用真实平台数据", value=False, help="通过 Playwright 浏览器自动化获取真实岗位数据")
        if use_real:
            st.caption("⚠️ 需要先安装 Playwright 浏览器: `playwright install chromium`")
            st.caption("首次使用需手动登录各平台，Cookie 会自动保存")

        st.divider()
        st.header("ℹ️ 环境状态")
        if not api_key:
            st.warning("DeepSeek API Key 未配置")
        else:
            try:
                from resume_matcher.ai.client import create_client
                client = create_client(api_key=api_key, base_url=base_url)
                models = client.models.list()
                model_ids = [m.id for m in models.data]
                st.success(f"DeepSeek API 已连接（{len(model_ids)} 个模型）")
                if model_ids:
                    st.caption(f"可用模型: {', '.join(model_ids)}")
            except Exception as e:
                st.error(f"DeepSeek API 连接失败: {e}")
                st.caption("请检查 API Key 和网络连接")

    # ── 主区域：输入 ──
    tab_upload, tab_input = st.tabs(["📄 上传简历", "✍️ 直接输入"])

    resume_file_path = None
    uploaded_text = None

    with tab_upload:
        uploaded_file = st.file_uploader(
            "上传简历文件",
            type=["pdf", "docx", "txt"],
            help="支持 PDF、Word (.docx)、纯文本 (.txt) 格式",
        )
        if uploaded_file:
            st.success(f"已上传: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

    with tab_input:
        uploaded_text = st.text_area(
            "粘贴简历内容",
            height=200,
            placeholder="在此粘贴你的简历全文...",
        )

    st.divider()

    # ── 搜索条件 ──
    st.subheader("🔍 搜索条件（可选）")
    col1, col2, col3 = st.columns(3)
    with col1:
        job_title = st.text_input("目标岗位", placeholder="如: Python工程师")
    with col2:
        location = st.text_input("期望地点", placeholder="如: 北京")
    with col3:
        keywords_str = st.text_input("关键词（逗号分隔）", placeholder="如: FastAPI, 微服务")

    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else []

    # ── 开始匹配按钮 ──
    st.divider()
    start_match = st.button("🚀 开始匹配", type="primary", use_container_width=True)

    if start_match:
        # 验证输入
        if not api_key:
            st.error("请先配置 DeepSeek API Key")
            return

        has_file = uploaded_file is not None
        has_text = uploaded_text and uploaded_text.strip()

        if not has_file and not has_text:
            st.error("请上传简历文件或粘贴简历内容")
            return

        # 准备简历文件
        if has_file:
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                resume_file_path = Path(tmp.name)
        elif has_text:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
                tmp.write(uploaded_text)
                resume_file_path = Path(tmp.name)

        criteria = SearchCriteria(
            job_title=job_title,
            keywords=keywords,
            location=location,
        )

        try:
            # Step 1: 解析简历
            with st.status("正在处理...", expanded=True) as status:
                st.write("📝 正在解析简历...")
                from resume_matcher.core.resume_parser import parse_resume
                resume = parse_resume(
                    resume_file_path,
                    model_name=model_name,
                    api_key=api_key,
                    base_url=base_url,
                )
                st.write(f"✅ 简历解析完成 - {resume.name}")

                # Step 2: 获取岗位
                st.write("📋 正在获取岗位数据...")
                from resume_matcher.platforms.registry import get_all_jobs
                platform_filter = None if platform == "all" else platform
                jobs = get_all_jobs(criteria, platform_filter=platform_filter, use_real=use_real)
                st.write(f"✅ 获取到 {len(jobs)} 个岗位")

                # Step 3: 匹配
                st.write("🤖 正在进行智能匹配...")
                from resume_matcher.core.matcher import match_jobs
                results = match_jobs(
                    resume=resume,
                    jobs=jobs,
                    criteria=criteria,
                    model_name=model_name,
                    api_key=api_key,
                    base_url=base_url,
                )
                st.write(f"✅ 匹配完成")
                status.update(label="处理完成!", state="complete")

            # 过滤和截取
            results = [r for r in results if r.score >= min_score]
            results = results[:top_n]

            if not results:
                st.warning("没有找到匹配的岗位，请尝试调整搜索条件。")
                return

            # ── 简历质量检查 ──
            warnings = []
            if not resume.skills or len(resume.skills) < 3:
                warnings.append("技能提取较少，匹配质量可能受影响")
            if not resume.summary:
                warnings.append("未提取到候选人画像摘要")
            if not resume.work_experience:
                warnings.append("未提取到工作经历")
            if warnings:
                st.warning("⚠️ 简历解析质量提醒：" + "；".join(warnings))

            # ── 展示简历解析结果 ──
            with st.expander("📝 简历解析结果", expanded=False):
                if resume.summary:
                    st.info(f"**候选人画像：** {resume.summary}")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**姓名:** {resume.name}")
                    st.write(f"**邮箱:** {resume.email}")
                    st.write(f"**电话:** {resume.phone}")
                    st.write(f"**地点:** {resume.location}")
                    if resume.seniority_level:
                        st.write(f"**资历等级:** {resume.seniority_level}")
                    if resume.job_category:
                        st.write(f"**岗位类别:** {resume.job_category}")
                    if resume.industry_domains:
                        st.write(f"**从业行业:** {', '.join(resume.industry_domains)}")
                with col_b:
                    if resume.skills:
                        st.write(f"**技能 ({len(resume.skills)} 项):** {', '.join(resume.skills)}")
                    if resume.education:
                        for edu in resume.education:
                            st.write(f"**教育:** {edu.school} - {edu.degree} {edu.major}")
                    if resume.work_experience:
                        for exp in resume.work_experience:
                            st.write(f"**工作:** {exp.company} - {exp.title}")
                    if resume.projects:
                        for proj in resume.projects:
                            st.write(f"**项目:** {proj.name}" + (f" ({proj.role})" if proj.role else ""))

            # ── 展示匹配结果 ──
            st.subheader(f"🏆 匹配结果（共 {len(results)} 条）")

            for i, result in enumerate(results, 1):
                job = result.job
                score_cls = _score_class(result.score)
                salary = _format_salary(job.salary.min_k, job.salary.max_k)
                platform_name = PLATFORM_NAMES.get(job.platform.value, job.platform.value)

                with st.container():
                    col_rank, col_info, col_score = st.columns([0.5, 6, 1.5])

                    with col_rank:
                        st.markdown(f"### #{i}")

                    with col_info:
                        if job.url:
                            st.markdown(f"**[{job.title}]({job.url})** @ {job.company}")
                        else:
                            st.markdown(f"**{job.title}** @ {job.company}")
                        st.caption(f"📍 {job.location}  |  💰 {salary}  |  📅 {job.experience_required}  |  🎓 {job.education_required}  |  🏷️ {platform_name}")

                    with col_score:
                        st.markdown(f'<p class="{score_cls}">{result.score:.0f} 分</p>', unsafe_allow_html=True)

                    # 详细信息展开
                    with st.expander("查看详情"):
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            st.write("**岗位描述:**")
                            st.write(job.description)
                            if job.must_have_skills:
                                st.write("**必须技能:**")
                                for skill in job.must_have_skills:
                                    st.write(f"- {skill}")
                            if job.nice_to_have_skills:
                                st.write("**加分技能:**")
                                for skill in job.nice_to_have_skills:
                                    st.write(f"- {skill}")
                            elif job.requirements:
                                st.write("**岗位要求:**")
                                for req in job.requirements:
                                    st.write(f"- {req}")
                            if job.seniority_level:
                                st.caption(f"资历要求: {job.seniority_level} | 岗位类别: {job.job_category}")
                            if job.url:
                                st.markdown(f"🔗 [查看岗位详情 →]({job.url})")
                        with detail_col2:
                            if result.match_reasons:
                                st.write("**✅ 匹配原因:**")
                                for reason in result.match_reasons:
                                    st.write(f"- {reason}")
                            if result.skill_overlap:
                                st.write(f"**🔗 技能重合:** {', '.join(result.skill_overlap)}")
                            if result.gaps:
                                st.write(f"**⚠️ 缺失项:** {', '.join(result.gaps)}")
                            if job.tags:
                                st.write(f"**🏷️ 福利标签:** {', '.join(job.tags)}")

                    st.divider()

        except Exception as e:
            st.error(f"处理出错: {e}")
            st.caption("请检查 DeepSeek API Key 和网络连接。运行 `resume-matcher doctor` 检查环境。")


if __name__ == "__main__":
    main()
