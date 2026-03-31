"""文件解析器测试"""

import tempfile
from pathlib import Path

import pytest

from resume_matcher.parsers.base import get_parser
from resume_matcher.parsers.txt_parser import TxtParser


def test_txt_parser():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("张三\nPython开发工程师\n技能：Python, Java")
        f.flush()
        parser = TxtParser()
        text = parser.parse(Path(f.name))
        assert "张三" in text
        assert "Python" in text


def test_get_parser_txt():
    parser = get_parser(Path("resume.txt"))
    assert isinstance(parser, TxtParser)


def test_get_parser_pdf():
    parser = get_parser(Path("resume.pdf"))
    from resume_matcher.parsers.pdf_parser import PdfParser
    assert isinstance(parser, PdfParser)


def test_get_parser_docx():
    parser = get_parser(Path("resume.docx"))
    from resume_matcher.parsers.docx_parser import DocxParser
    assert isinstance(parser, DocxParser)


def test_get_parser_unsupported():
    with pytest.raises(ValueError, match="不支持的文件格式"):
        get_parser(Path("resume.jpg"))
