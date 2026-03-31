"""PDF 文件解析器"""

from pathlib import Path

import pymupdf


class PdfParser:
    """使用 PyMuPDF 提取 PDF 文本"""

    def parse(self, file_path: Path) -> str:
        doc = pymupdf.open(str(file_path))
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
