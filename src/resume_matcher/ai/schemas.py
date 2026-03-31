"""AI 输出的 JSON Schema 定义"""

# 简历解析输出的 JSON Schema
RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string"},
        "location": {"type": "string"},
        "summary": {"type": "string"},
        "seniority_level": {"type": "string"},
        "job_category": {"type": "string"},
        "industry_domains": {"type": "array", "items": {"type": "string"}},
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": "string"},
                    "major": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["school", "degree", "major"],
            },
        },
        "work_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["company", "title"],
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                    "tech_stack": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name"],
            },
        },
        "skills": {"type": "array", "items": {"type": "string"}},
        "certifications": {"type": "array", "items": {"type": "string"}},
        "languages": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "skills", "summary"],
}

# 岗位匹配输出的 JSON Schema
MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 100},
                    "match_reasons": {"type": "array", "items": {"type": "string"}},
                    "skill_overlap": {"type": "array", "items": {"type": "string"}},
                    "gaps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["job_id", "score", "match_reasons"],
            },
        }
    },
    "required": ["results"],
}
