"""纯文本文件解析器"""

from pathlib import Path


class TxtParser:
    """读取纯文本文件"""

    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8").strip()
