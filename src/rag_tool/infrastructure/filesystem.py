from collections.abc import Iterator
from pathlib import Path
import os
import stat


class MarkdownFolderSource:
    def list_markdown(self, folder: Path) -> Iterator[Path]:
        folder = folder.resolve()
        if not folder.is_dir():
            raise NotADirectoryError(f"not a directory: {folder}")
        def raise_scan_error(error: OSError) -> None:
            raise error

        # rglob can silently suppress traversal errors, making cleanup unsafe.
        paths = []
        for directory, _, names in os.walk(folder, onerror=raise_scan_error, followlinks=False):
            for name in names:
                path = Path(directory) / name
                if name.endswith(".md") and stat.S_ISREG(path.stat().st_mode):
                    paths.append(path)
        yield from sorted(paths)

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")
