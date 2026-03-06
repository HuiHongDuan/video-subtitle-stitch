from dataclasses import dataclass
from typing import Iterable, List

@dataclass
class Segment:
    start: float
    end: float
    text: str

_PUNCT = set('，。！？；：、,.!?;: ')


def _format_ts(t: float) -> str:
    ms = int(round(t * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def wrap_zh(text: str, max_chars_per_line: int, max_lines: int) -> str:
    text = (text or '').strip()
    if not text:
        return ''
    lines: List[str] = []
    i = 0
    n = len(text)
    while i < n and len(lines) < max_lines:
        j = min(i + max_chars_per_line, n)
        if j < n:
            k = j
            while k > i and text[k - 1] not in _PUNCT:
                k -= 1
            if k == i:
                k = j
            line = text[i:k].strip()
            i = k
        else:
            line = text[i:j].strip()
            i = j
        if line:
            lines.append(line)
    return '\n'.join(lines[:max_lines])


def segments_to_srt(segments: Iterable[Segment], max_chars_per_line: int = 18, max_lines: int = 2) -> str:
    out: List[str] = []
    idx = 1
    for seg in segments:
        txt = wrap_zh(seg.text, max_chars_per_line, max_lines)
        if not txt:
            continue
        out.append(str(idx))
        out.append(f'{_format_ts(seg.start)} --> {_format_ts(seg.end)}')
        out.append(txt)
        out.append('')
        idx += 1
    return '\n'.join(out).strip() + '\n'
