import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Tuple

@dataclass
class SrtItem:
    start: float
    end: float
    text: str

_TS_RE = re.compile(r'(\d+):(\d+):(\d+),(\d+)')
_LINE_TS_RE = re.compile(r'(.+?)\s*-->\s*(.+)')


def _ts_to_seconds(ts: str) -> float:
    m = _TS_RE.search(ts.strip())
    if not m:
        raise ValueError(f'Bad timestamp: {ts}')
    h, mi, s, ms = map(int, m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000.0


def parse_srt(text: str) -> List[SrtItem]:
    blocks = [b.strip() for b in re.split(r'\n\s*\n', text.strip()) if b.strip()]
    items: List[SrtItem] = []
    for b in blocks:
        lines = [ln.rstrip() for ln in b.splitlines() if ln.strip() != '']
        if len(lines) < 3:
            continue
        ts_line = lines[0] if _LINE_TS_RE.search(lines[0]) else lines[1]
        txt_lines = lines[1:] if _LINE_TS_RE.search(lines[0]) else lines[2:]
        m = _LINE_TS_RE.search(ts_line)
        if not m:
            continue
        items.append(
            SrtItem(
                start=_ts_to_seconds(m.group(1)),
                end=_ts_to_seconds(m.group(2)),
                text=' '.join(txt_lines).strip(),
            )
        )
    return items


def _norm_text(s: str) -> str:
    s = (s or '').lower()
    s = re.sub(r'[\s\u3000]', '', s)
    s = re.sub(r"[，。！？；：、,.!?;:「」『』（）()\[\]{}<>《》“”'`~…—-]", '', s)
    return s


def text_similarity(a: str, b: str) -> float:
    a2, b2 = _norm_text(a), _norm_text(b)
    if not a2 and not b2:
        return 1.0
    if not a2 or not b2:
        return 0.0
    return SequenceMatcher(None, a2, b2).ratio()


def overlap_iou(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    a0, a1 = a
    b0, b1 = b
    inter = max(0.0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union > 0 else 0.0


def evaluate_srt(pred_text: str, gold_text: str, min_iou: float = 0.5) -> dict:
    pred = parse_srt(pred_text)
    gold = parse_srt(gold_text)
    if not gold:
        return {'coverage': 0.0, 'avg_similarity': 0.0, 'score': 0.0, 'gold': 0, 'matched': 0}
    matched = 0
    sim_sum = 0.0
    for g in gold:
        best_iou = 0.0
        best_sim = 0.0
        for p in pred:
            iou = overlap_iou((p.start, p.end), (g.start, g.end))
            if iou > best_iou:
                best_iou = iou
                best_sim = text_similarity(p.text, g.text)
        if best_iou >= min_iou:
            matched += 1
            sim_sum += best_sim
    coverage = matched / len(gold)
    avg_similarity = (sim_sum / matched) if matched else 0.0
    return {
        'coverage': coverage,
        'avg_similarity': avg_similarity,
        'score': coverage * avg_similarity,
        'gold': len(gold),
        'matched': matched,
        'min_iou': min_iou,
    }
