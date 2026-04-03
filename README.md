# 🎯 Resume Matcher - 智能岗位匹配--工作来找你！

> 厌倦了在boss直聘上逐个点开岗位读jd再失望退出吗？🙍
> 智能岗位匹配模式借助大模型，同时分析简历特征和岗位jd
> 帮助你找到最匹配自己简历的岗位😺

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-green.svg)](https://deepseek.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 核心功能

### 🤖 AI 简历深度解析
- 支持 **PDF / Word / 纯文本** 三种简历格式
- 自动提取姓名、联系方式、教育背景、工作经历、项目经验、技能清单
- AI 生成候选人画像摘要，判断资历等级和适合的岗位方向

### 🔍 多平台岗位获取
- 内置 **208 条高质量模拟岗位数据**，开箱即用
- 支持真实平台数据采集（基于 Playwright 浏览器自动化）：
  - 🟢 Boss直聘
  - 🟢 猎聘
  - 🟢 前程无忧
  - 🔵 智联招聘（模拟数据）
  - 🔵 拉勾（模拟数据）
- Cookie 持久化，登录一次即可重复使用

### 🎯 智能匹配评分
- **五维评分体系**：必须技能覆盖率(30%) + 经验相关度(25%) + 项目深度(20%) + 加分项匹配(15%) + 成长适配(10%)
- **硬性过滤规则**：岗位类别不匹配自动降分，资历等级差距过大自动降分
- 输出匹配原因、技能重合、能力缺口等详细分析

### 💻 双端交互
- **CLI 命令行**：适合开发者，支持 JSON 输出，可集成到自动化流程
- **Web 界面**：基于 Streamlit，拖拽上传简历，可视化展示匹配结果

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- [DeepSeek API Key](https://platform.deepseek.com/)（用于 AI 解析和匹配）

### 安装

```bash
git clone https://github.com/GYX1616/resume-matcher.git
cd resume-matcher
pip install -e .
```

### 配置 API Key

```bash
# 方式一：命令行配置
resume-matcher config set deepseek_api_key sk-你的API密钥

# 方式二：创建 .env 文件
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 检查环境

```bash
resume-matcher doctor
```

---

## 📖 使用方式

### 方式一：CLI 命令行

#### 解析简历

```bash
# 解析简历，查看提取结果
resume-matcher parse 我的简历.pdf

# 输出 JSON 格式
resume-matcher parse 我的简历.pdf --json
```

#### 匹配岗位

```bash
# 基础匹配（使用模拟数据）
resume-matcher scan 我的简历.pdf

# 指定目标岗位和地点
resume-matcher scan 我的简历.pdf -t "Python工程师" -l "北京"

# 添加关键词筛选
resume-matcher scan 我的简历.pdf -t "后端开发" -k FastAPI -k 微服务

# 只看 Boss直聘 的岗位，最低 70 分
resume-matcher scan 我的简历.pdf -p boss -s 70

# 使用真实平台数据
resume-matcher scan 我的简历.pdf --real

# 显示详细匹配分析
resume-matcher scan 我的简历.pdf -v
```

#### 平台登录（使用真实数据前需要）

```bash
# 登录 Boss直聘
resume-matcher login boss

# 登录猎聘
resume-matcher login liepin

# 登录前程无忧
resume-matcher login job51
```

#### 配置管理

```bash
# 查看当前配置
resume-matcher config show

# 修改配置
resume-matcher config set deepseek_model deepseek-chat
resume-matcher config set default_top_n 20
```

### 方式二：Web 界面

```bash
python3 -m streamlit run src/resume_matcher/web/app.py
```

打开浏览器访问 `http://localhost:8501`，即可使用可视化界面：

1. 上传简历或粘贴简历内容
2. 设置搜索条件（可选）
3. 点击「开始匹配」
4. 查看匹配结果和详细分析

---

## 🏗️ 技术架构

```
resume-matcher/
├── src/resume_matcher/
│   ├── ai/                    # AI 层
│   │   ├── client.py          # DeepSeek API 客户端（OpenAI 兼容）
│   │   ├── prompts.py         # Prompt 模板
│   │   └── schemas.py         # JSON Schema 定义
│   ├── core/                  # 核心逻辑
│   │   ├── models.py          # Pydantic 数据模型
│   │   ├── config.py          # 配置管理
│   │   ├── resume_parser.py   # 简历解析引擎
│   │   └── matcher.py         # 匹配引擎（批量处理）
│   ├── parsers/               # 文件解析器
│   │   ├── pdf_parser.py      # PDF 解析（PyMuPDF）
│   │   ├── docx_parser.py     # Word 解析（python-docx）
│   │   └── txt_parser.py      # 纯文本解析
│   ├── platforms/             # 平台适配层
│   │   ├── boss_platform.py   # Boss直聘
│   │   ├── liepin_platform.py # 猎聘
│   │   ├── job51_platform.py  # 前程无忧
│   │   └── mock_platform.py   # 模拟数据
│   ├── cli/                   # 命令行界面
│   │   ├── app.py             # CLI 入口
│   │   ├── commands/          # 子命令
│   │   └── display.py         # Rich 终端渲染
│   └── web/                   # Web 界面
│       └── app.py             # Streamlit 应用
├── scripts/
│   └── enrich_mock_jobs.py    # 岗位数据扩充脚本
└── tests/                     # 测试
```

### 数据流

```
简历文件 → 文件解析器 → 原始文本 → DeepSeek AI → 结构化简历
                                                      ↓
搜索条件 → 平台适配器 → 岗位列表 → 匹配引擎(AI) → 评分排序 → 结果展示
```

---

## ⚙️ 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `DEEPSEEK_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |
| `DEFAULT_TOP_N` | 默认显示结果数 | `10` |
| `DEFAULT_PLATFORM` | 默认平台 | `all` |

---

## 📊 匹配评分说明

| 分数区间 | 匹配等级 | 含义 |
|----------|----------|------|
| 90-100 | 🟢 完美匹配 | 技能、经验、行业高度吻合 |
| 70-89 | 🟢 强匹配 | 核心要求满足，少量 gap |
| 50-69 | 🟡 中等匹配 | 部分技能相关，有明显 gap |
| 30-49 | 🟠 弱匹配 | 少量技能重合，方向有偏差 |
| 0-29 | 🔴 不匹配 | 技能、经验、方向均不吻合 |

---

## 🛡️ 隐私安全

- 简历数据**仅在本地处理**，不会上传到任何第三方服务器
- AI 解析通过 DeepSeek API 进行，数据传输使用 HTTPS 加密
- 平台登录 Cookie 保存在本地 `~/.resume-matcher/cookies/` 目录
- `.env` 文件已加入 `.gitignore`，API Key 不会被提交到代码仓库

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License
