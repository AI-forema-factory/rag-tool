from collections.abc import Iterator
from pathlib import Path


class MarkdownFolderSource:
    def list_markdown(self, folder: Path) -> Iterator[Path]:
        folder = folder.resolve()
        if not folder.is_dir():
            raise NotADirectoryError(f"not a directory: {folder}")
        yield from sorted(p for p in folder.rglob("*.md") if p.is_file())

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")
