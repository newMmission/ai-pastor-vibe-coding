# -*- coding: utf-8 -*-
"""설교본 안의 성경 장절을 모두 찾아, 실제로 있는 장절인지 검사한다. (AI를 쓰지 않는 프로그램)

검사는 최윤식 박사의 verify_bible.py(교정본)를 그대로 쓴다.
- 장·절이 실제로 있는가 (개역개정 66권 기준)
- 사본학적으로 주의할 본문인가 (막 16:9-20 같은 곳)

쓰는 법:  py 도구/장절검사.py 설교/2026-11-22_주일설교/설교본_v01.md
Copyright (c) 2026 newMmission (뉴엠미션) — MIT License
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_bible as vb  # noqa: E402

# 정식 이름과 약어를 긴 것부터 (예: '요한일서'가 '요'보다 먼저 잡히도록)
_NAMES = sorted(set(vb.ALL_BOOKS) | set(vb.BOOK_ABBR_KO), key=len, reverse=True)
_PATTERN = re.compile(
    r"(?<![가-힣])(" + "|".join(map(re.escape, _NAMES)) + r")\s*"
    r"(\d{1,3})\s*(?::|장|편)\s*"
    r"(?:(\d{1,3})\s*절?)?"
    r"(?:\s*[-~–]\s*(\d{1,3})\s*절?)?"
)


def find_references(text):
    """본문에서 '에스겔 16:6', '겔 16장 6절', '시편 23편 4절', '고후 4:8-9' 같은 장절을 찾는다."""
    found = []
    for m in _PATTERN.finditer(text):
        book, ch, vs, ve = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        # 한 글자 약어(시, 요, 사 …)는 뒤에 ':'이 있을 때만 장절로 본다 — 보통 낱말과 헷갈리지 않게
        if len(book) == 1 and ":" not in m.group(0):
            continue
        found.append((m.group(0).strip(), book, ch, int(vs) if vs else None, int(ve) if ve else None))
    return found


def check_text(text):
    """찾은 장절마다 검사 결과를 돌려준다."""
    results = []
    seen = set()
    for shown, book, ch, vs, ve in find_references(text):
        key = (vb.normalize_book(book), ch, vs, ve)
        if key in seen:
            continue
        seen.add(key)
        r = vb.validate_reference(book, ch, vs, ve)
        flag = vb.flag_textual_critical(book, ch, vs or 1, ve or vs or 1) if r["ok"] else None
        results.append({
            "본문에 적힌 대로": shown,
            "정식 이름": r.get("canonical") or book,
            "결과": "맞음" if r["ok"] else "틀림",
            "까닭": r.get("reason") or "",
            "사본학 주의": flag or "",
        })
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("쓰는 법: py 도구/장절검사.py <설교본 파일>")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    rows = check_text(text)
    if not rows:
        print("장절을 찾지 못했습니다.")
    for row in rows:
        print(f"[{row['결과']}] {row['본문에 적힌 대로']}  {row['까닭']} {row['사본학 주의']}")
