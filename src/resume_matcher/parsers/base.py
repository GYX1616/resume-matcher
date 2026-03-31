"""文件解析器基类"""

from pathlib import Path
from typing import Protocol


class FileParser(Protocol):
    """文件解析器协议"""

    def parse(self, file_path: Path) -> str:
        """从文件中提取纯文本内容"""
        ...


def get_parser(file_path: Path) -> FileParser:
    """根据文件扩展名返回对应的解析器"""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        from resume_matcher.parsers.pdf_parser import PdfParser
        return PdfParser()
    elif suffix == ".docx":
        from resume_matcher.parsers.docx_parser import DocxParser
        return DocxParser()
    elif suffix == ".txt":
        from resume_matcher.parsers.txt_parser import TxtParser
        return TxtParser()
    else:
        raise ValueError(f"不支持的文件格式: {suffix}（支持 .pdf, .docx, .txt）")
