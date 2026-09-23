"""Markdown chunking: split on headings, then pack paragraphs up to a size budget.

Every chunk records the 1-indexed, inclusive line span it came from so a caller
can jump straight to the source.
"""

import re

from rag_tool.domain.models import Chunk

_HEADING = re.compile(r"^#{1,6}\s")
_FENCE = re.compile(r"^(```|~~~)")


def chunk_markdown(source_path: str, text: str, max_chars: int = 1200) -> list[Chunk]:
    lines = text.splitlines()
    chunks: list[Chunk] = []
    for section in _sections(lines):
        chunks.extend(_pack(source_path, lines, section, max_chars))
    return chunks


def _sections(lines: list[str]) -> list[tuple[int, int]]:
    """Return (start, end) 0-indexed half-open spans, each starting at a heading."""
    bounds: list[int] = [0]
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and i > 0 and _HEADING.match(line):
            bounds.append(i)
    bounds.append(len(lines))
    return [(a, b) for a, b in zip(bounds, bounds[1:]) if a < b]


def _paragraphs(lines: list[str], start: int, end: int) -> list[tuple[int, int]]:
    """Blank-line separated blocks within [start, end), never splitting a code fence."""
    blocks: list[tuple[int, int]] = []
    block_start: int | None = None
    in_fence = False
    for i in range(start, end):
        line = lines[i]
        if _FENCE.match(line):
            in_fence = not in_fence
        blank = not line.strip() and not in_fence
        if blank:
            if block_start is not None:
                blocks.append((block_start, i))
                block_start = None
        elif block_start is None:
            block_start = i
    if block_start is not None:
        blocks.append((block_start, end))
    return blocks


def _pack(source_path: str, lines: list[str], section: tuple[int, int], max_chars: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    cur_start: int | None = None
    cur_end = 0
    cur_len = 0

    def flush() -> None:
        if cur_start is None:
            return
        body = "\n".join(lines[cur_start:cur_end]).strip()
        if body:
            chunks.append(Chunk(source_path, cur_start + 1, cur_end, body))

    for p_start, p_end in _paragraphs(lines, *section):
        p_len = sum(len(line) + 1 for line in lines[p_start:p_end])
        if cur_start is not None and cur_len + p_len > max_chars:
            flush()
            cur_start = None
        if cur_start is None:
            cur_start, cur_len = p_start, 0
        cur_end = p_end
        cur_len += p_len
    flush()
    return chunks
