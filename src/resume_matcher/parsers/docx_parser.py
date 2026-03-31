"""Word 文件解析器"""

from pathlib import Path

from docx import Document


class DocxParser:
    """使用 python-docx 提取 Word 文档文本"""

    def parse(self, file_path: Path) -> str:
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
