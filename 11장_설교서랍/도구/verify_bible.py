# [설교서랍 교정본] 원본: 최윤식, cys-claude-sermon-skills (MIT License) — 참고/LICENSE-cys.txt
# newMmission(뉴엠미션)이 Windows(py 명령)에서 쓰도록 넣은 것. 성경 장절 검사 도구.
"""sermon-topic-message-coach 결정론 검증 모듈.

LLM 자연어 추론으로 처리하면 할루시네이션이 발생하기 쉬운 항목을
파이썬 lookup·범위 검사·존재 검증으로 환원한다.

검증 가능한 항목
----------------
- validate_reference(): 책·장·절 존재 검증 (할루시네이션 핵심 차단)
- normalize_book(): 약어·영문 → 정식 한국어 책명
- is_old_testament() / is_new_testament(): 정경 분류
- check_balance(): 5단계 구절 추천 균형 검증 (구약 1-2개, 신약 3-4개)
- flag_textual_critical(): 사본학 경계선 본문 자동 플래그
- count_korean_chars() / validate_message_length(): 25-45자 검증
- validate_pattern_distribution(): 5결 매트릭스 패턴 A/B/C/D 분포 검증
- get_sermon_style(): 7가지 작성법 번호 → 명칭 매핑
- self_check(): 데이터 무결성 자체 검증

데이터 출처
-----------
- 대한성서공회 『개역개정 4판』 (2005)
- NA28 (Nestle-Aland 28th edition), BHS (Biblia Hebraica Stuttgartensia)
- 위키피디아 "Chapters and verses of the Bible" (학계 공통)
"""

from __future__ import annotations

from typing import Optional

from bible_data import CHAPTER_VERSES, OT_BOOKS_ORDERED, NT_BOOKS_ORDERED


OT_BOOKS = set(OT_BOOKS_ORDERED)
NT_BOOKS = set(NT_BOOKS_ORDERED)
ALL_BOOKS = OT_BOOKS | NT_BOOKS


# ---------------------------------------------------------------------------
# 1. 책 약어 정규화 — 한국 개신교 표준 + 영문 보조
# ---------------------------------------------------------------------------
BOOK_ABBR_KO: dict[str, str] = {
    # 구약
    "창": "창세기", "출": "출애굽기", "레": "레위기", "민": "민수기", "신": "신명기",
    "수": "여호수아", "삿": "사사기", "룻": "룻기",
    "삼상": "사무엘상", "삼하": "사무엘하",
    "왕상": "열왕기상", "왕하": "열왕기하",
    "대상": "역대상", "대하": "역대하",
    "스": "에스라", "느": "느헤미야", "에": "에스더",
    "욥": "욥기", "시": "시편", "잠": "잠언", "전": "전도서", "아": "아가",
    "사": "이사야", "렘": "예레미야", "애": "예레미야애가",
    "겔": "에스겔", "단": "다니엘",
    "호": "호세아", "욜": "요엘", "암": "아모스", "옵": "오바댜",
    "욘": "요나", "미": "미가", "나": "나훔", "합": "하박국",
    "습": "스바냐", "학": "학개", "슥": "스가랴", "말": "말라기",
    # 신약
    "마": "마태복음", "막": "마가복음", "눅": "누가복음", "요": "요한복음",
    "행": "사도행전", "롬": "로마서",
    "고전": "고린도전서", "고후": "고린도후서",
    "갈": "갈라디아서", "엡": "에베소서", "빌": "빌립보서",
    "골": "골로새서",
    "살전": "데살로니가전서", "살후": "데살로니가후서",
    "딤전": "디모데전서", "딤후": "디모데후서",
    "딛": "디도서", "몬": "빌레몬서",
    "히": "히브리서", "약": "야고보서",
    "벧전": "베드로전서", "벧후": "베드로후서",
    "요일": "요한일서", "요이": "요한이서", "요삼": "요한삼서",
    "유": "유다서", "계": "요한계시록",
}

BOOK_ABBR_EN: dict[str, str] = {
    "gen": "창세기", "exo": "출애굽기", "lev": "레위기", "num": "민수기", "deu": "신명기", "dt": "신명기",
    "jos": "여호수아", "josh": "여호수아", "jdg": "사사기", "judg": "사사기", "rut": "룻기", "ruth": "룻기",
    "1sa": "사무엘상", "1sam": "사무엘상", "2sa": "사무엘하", "2sam": "사무엘하",
    "1ki": "열왕기상", "1kgs": "열왕기상", "2ki": "열왕기하", "2kgs": "열왕기하",
    "1ch": "역대상", "1chr": "역대상", "2ch": "역대하", "2chr": "역대하",
    "ezr": "에스라", "ezra": "에스라", "neh": "느헤미야", "est": "에스더",
    "job": "욥기", "psa": "시편", "ps": "시편", "psalm": "시편",
    "pro": "잠언", "prov": "잠언", "ecc": "전도서", "eccl": "전도서", "sng": "아가", "song": "아가",
    "isa": "이사야", "jer": "예레미야", "lam": "예레미야애가",
    "eze": "에스겔", "ezk": "에스겔", "ezek": "에스겔", "dan": "다니엘",
    "hos": "호세아", "joe": "요엘", "joel": "요엘", "amo": "아모스", "amos": "아모스",
    "oba": "오바댜", "obad": "오바댜",
    "jon": "요나", "jonah": "요나", "mic": "미가", "mica": "미가",
    "nah": "나훔", "nahum": "나훔", "hab": "하박국", "habak": "하박국",
    "zep": "스바냐", "zeph": "스바냐", "hag": "학개", "hagg": "학개",
    "zec": "스가랴", "zech": "스가랴", "mal": "말라기",
    "mat": "마태복음", "matt": "마태복음", "mt": "마태복음",
    "mar": "마가복음", "mrk": "마가복음", "mark": "마가복음", "mk": "마가복음",
    "luk": "누가복음", "luke": "누가복음", "lk": "누가복음",
    "jhn": "요한복음", "joh": "요한복음", "john": "요한복음", "jn": "요한복음",
    "act": "사도행전", "acts": "사도행전", "rom": "로마서",
    "1co": "고린도전서", "1cor": "고린도전서", "2co": "고린도후서", "2cor": "고린도후서",
    "gal": "갈라디아서", "eph": "에베소서", "ephes": "에베소서",
    "phi": "빌립보서", "php": "빌립보서", "phil": "빌립보서",
    "col": "골로새서",
    "1th": "데살로니가전서", "1thes": "데살로니가전서", "2th": "데살로니가후서", "2thes": "데살로니가후서",
    "1ti": "디모데전서", "1tim": "디모데전서", "2ti": "디모데후서", "2tim": "디모데후서",
    "tit": "디도서", "titus": "디도서", "phm": "빌레몬서", "phlm": "빌레몬서",
    "heb": "히브리서", "jam": "야고보서", "jas": "야고보서", "jms": "야고보서",
    "1pe": "베드로전서", "1pet": "베드로전서", "2pe": "베드로후서", "2pet": "베드로후서",
    "1jn": "요한일서", "1jo": "요한일서", "1joh": "요한일서",
    "2jn": "요한이서", "2jo": "요한이서", "2joh": "요한이서",
    "3jn": "요한삼서", "3jo": "요한삼서", "3joh": "요한삼서",
    "jud": "유다서", "jude": "유다서", "rev": "요한계시록", "revel": "요한계시록",
}


def normalize_book(book_input: str) -> Optional[str]:
    """입력된 책 이름(약어·정식·영문)을 정식 한국어 책명으로 변환.

    실패 시 None 반환.
    """
    if not book_input:
        return None
    key = book_input.strip()
    if key in ALL_BOOKS:
        return key
    if key in BOOK_ABBR_KO:
        return BOOK_ABBR_KO[key]
    # 영문 입력 (대소문자 무시, 공백·점 제거)
    norm = key.lower().replace(" ", "").replace(".", "").replace("'", "")
    if norm in BOOK_ABBR_EN:
        return BOOK_ABBR_EN[norm]
    # 부분 일치 (앞 3-5글자)
    for prefix_len in (5, 4, 3):
        prefix = norm[:prefix_len]
        if prefix in BOOK_ABBR_EN:
            return BOOK_ABBR_EN[prefix]
    return None


# ---------------------------------------------------------------------------
# 2. 정경 분류
# ---------------------------------------------------------------------------
def is_old_testament(book_input: str) -> bool:
    canonical = normalize_book(book_input)
    return canonical in OT_BOOKS if canonical else False


def is_new_testament(book_input: str) -> bool:
    canonical = normalize_book(book_input)
    return canonical in NT_BOOKS if canonical else False


# ---------------------------------------------------------------------------
# 3. 책·장·절 존재 검증 (할루시네이션 차단 핵심)
# ---------------------------------------------------------------------------
def get_chapter_count(book_input: str) -> Optional[int]:
    canonical = normalize_book(book_input)
    if not canonical:
        return None
    chapters = CHAPTER_VERSES.get(canonical)
    return len(chapters) if chapters else None


def get_verse_count(book_input: str, chapter: int) -> Optional[int]:
    canonical = normalize_book(book_input)
    if not canonical:
        return None
    chapters = CHAPTER_VERSES.get(canonical)
    if not chapters:
        return None
    if not (1 <= chapter <= len(chapters)):
        return None
    return chapters[chapter - 1]


def validate_reference(
    book_input: str,
    chapter: int,
    verse_start: Optional[int] = None,
    verse_end: Optional[int] = None,
) -> dict:
    """성경 인용의 책·장·절 존재 검증.

    반환:
        {ok, canonical, max_chapter, max_verse, testament, reason}
    """
    canonical = normalize_book(book_input)
    if not canonical:
        return {
            "ok": False,
            "canonical": None,
            "max_chapter": None,
            "max_verse": None,
            "testament": None,
            "reason": f"'{book_input}'은(는) 정경 66권에서 찾을 수 없는 책 이름·약어입니다.",
        }
    testament = "구약" if canonical in OT_BOOKS else "신약"
    chapters = CHAPTER_VERSES.get(canonical)
    if not chapters:
        return {
            "ok": False,
            "canonical": canonical,
            "max_chapter": None,
            "max_verse": None,
            "testament": testament,
            "reason": f"{canonical}의 장별 절수 데이터가 등록되지 않음 (bible_data.py 보완 필요).",
        }
    max_chapter = len(chapters)
    if not (1 <= chapter <= max_chapter):
        return {
            "ok": False,
            "canonical": canonical,
            "max_chapter": max_chapter,
            "max_verse": None,
            "testament": testament,
            "reason": f"{canonical}은(는) 총 {max_chapter}장까지 있습니다. {chapter}장은 존재하지 않습니다.",
        }
    max_verse = chapters[chapter - 1]
    if verse_start is None:
        return {
            "ok": True,
            "canonical": canonical,
            "max_chapter": max_chapter,
            "max_verse": max_verse,
            "testament": testament,
            "reason": None,
        }
    if not (1 <= verse_start <= max_verse):
        return {
            "ok": False,
            "canonical": canonical,
            "max_chapter": max_chapter,
            "max_verse": max_verse,
            "testament": testament,
            "reason": (
                f"{canonical} {chapter}장은 총 {max_verse}절까지 있습니다. "
                f"{verse_start}절은 존재하지 않습니다."
            ),
        }
    if verse_end is not None:
        if verse_end < verse_start:
            return {
                "ok": False,
                "canonical": canonical,
                "max_chapter": max_chapter,
                "max_verse": max_verse,
                "testament": testament,
                "reason": f"절 범위 끝({verse_end})이 시작({verse_start})보다 작을 수 없습니다.",
            }
        if verse_end > max_verse:
            return {
                "ok": False,
                "canonical": canonical,
                "max_chapter": max_chapter,
                "max_verse": max_verse,
                "testament": testament,
                "reason": (
                    f"{canonical} {chapter}장은 총 {max_verse}절까지 있습니다. "
                    f"{verse_end}절은 존재하지 않습니다."
                ),
            }
    return {
        "ok": True,
        "canonical": canonical,
        "max_chapter": max_chapter,
        "max_verse": max_verse,
        "testament": testament,
        "reason": None,
    }


# ---------------------------------------------------------------------------
# 4. 5단계 추천 균형 검증 (Gate 5 결정론 환원)
# ---------------------------------------------------------------------------
def check_balance(references: list[tuple[str, int, Optional[int], Optional[int]]]) -> dict:
    """추천된 5개 구절의 구약/신약 균형과 책 다양성 검증.

    인자: [(book, chapter, verse_start, verse_end), ...] (개수 무관)

    반환: {ok, ot_count, nt_count, books, warnings, invalid}
    """
    from collections import Counter

    warnings: list[str] = []
    invalid: list[dict] = []
    ot_count = 0
    nt_count = 0
    books: list[str] = []
    for idx, ref in enumerate(references, start=1):
        book, chap, vs, ve = ref
        v = validate_reference(book, chap, vs, ve)
        if not v["ok"]:
            invalid.append({"index": idx, "input": ref, "reason": v["reason"]})
            continue
        books.append(v["canonical"])
        if v["testament"] == "구약":
            ot_count += 1
        else:
            nt_count += 1

    if len(references) == 5:
        if not (1 <= ot_count <= 2):
            warnings.append(
                f"5개 구절 중 구약 비중 권장(1-2개)을 벗어남 (현재 {ot_count}개). "
                "메시지가 구약 주제(언약·출애굽 등)면 명시적 조정 가능."
            )
        if not (3 <= nt_count <= 4):
            warnings.append(
                f"5개 구절 중 신약 비중 권장(3-4개)을 벗어남 (현재 {nt_count}개)."
            )

    if books:
        book_counter = Counter(books)
        most_common_book, most_common_count = book_counter.most_common(1)[0]
        if most_common_count >= 3:
            warnings.append(
                f"한 책('{most_common_book}')에 {most_common_count}개 몰림 — 다양성 권장 조정."
            )

    return {
        "ok": len(invalid) == 0,
        "ot_count": ot_count,
        "nt_count": nt_count,
        "books": books,
        "warnings": warnings,
        "invalid": invalid,
    }


# ---------------------------------------------------------------------------
# 5. 사본학 경계선 본문 자동 플래그
# ---------------------------------------------------------------------------
# (book, chapter, verse_start, verse_end_or_None, note)
# 학계 표준 본문비평 자료 (NA28, UBS5, BHQ, Metzger Textual Commentary)에
# 명시된 경계선 본문.
TEXTUAL_CRITICAL_PASSAGES: list[tuple[str, int, int, Optional[int], str]] = [
    # 신약
    ("마가복음", 16, 9, 20,
     "긴 결말 (Longer Ending). 시내·바티칸 사본 등 핵심 사본에 없음. NA28에 [이중 대괄호] 표기. 강해 시 사본학적 위치 안내 권장."),
    ("요한복음", 7, 53, None,
     "Pericope Adulterae (요 7:53-8:11). P66, P75, 시내·바티칸 사본 등에 없음. NA28에 [이중 대괄호]."),
    ("요한복음", 8, 1, 11,
     "Pericope Adulterae (요 7:53-8:11). 후대 첨가설 다수. NA28에 [이중 대괄호]. 강단 사용 가능하되 사본학 위치 안내 권장."),
    ("누가복음", 23, 34, 34,
     "눅 23:34a '아버지여 저들을 사하여 주옵소서'. P75 등 일부 초기 사본에 빠짐. NA28에 [이중 대괄호]. 정통 강단에서 인정·사용."),
    ("요한복음", 5, 3, 4,
     "베데스다 천사 (요 5:3b-4). 후대 첨가. NA28 본문에 없으며 각주 처리."),
    ("사도행전", 8, 37, None,
     "에디오피아 내시 신앙고백. NA28 본문에 없음 — Western Text 전통."),
    ("마태복음", 17, 21, None,
     "이런 종류는 기도·금식. NA28 본문에 없음. 막 9:29 평행 본문에서 들어온 것으로 봄."),
    ("마태복음", 18, 11, None,
     "잃은 자 구원. NA28 본문에 없음. 눅 19:10 평행 본문에서 들어온 것."),
    ("마태복음", 23, 14, None,
     "과부 가산 삼킴. NA28 본문에 없음."),
    ("마가복음", 7, 16, None,
     "들을 귀 있는 자는 들으라. NA28 본문에 없음."),
    ("마가복음", 9, 44, None,
     "꺼지지 않는 불 (9:44, 9:46). NA28 본문에 없음."),
    ("마가복음", 9, 46, None,
     "꺼지지 않는 불 (9:44, 9:46). NA28 본문에 없음."),
    ("마가복음", 11, 26, None,
     "너희가 용서하지 않으면. NA28 본문에 없음. 마 6:15에서 들어온 것."),
    ("마가복음", 15, 28, None,
     "그가 범죄자 중 하나로. NA28 본문에 없음."),
    ("누가복음", 17, 36, None,
     "두 사람이 밭에 있음. NA28 본문에 없음. 마 24:40 평행에서 들어옴."),
    ("누가복음", 23, 17, None,
     "명절에 한 사람 놓아주는 전례. NA28 본문에 없음. 마 27:15·막 15:6 평행에서."),
    ("사도행전", 15, 34, None,
     "실라가 그곳에 머무름. NA28 본문에 없음."),
    ("사도행전", 24, 7, None,
     "루시아 천부장 부분 (24:6b-8a). NA28 본문에 없음."),
    ("사도행전", 28, 29, None,
     "유대인들이 떠나감. NA28 본문에 없음."),
    ("로마서", 16, 24, None,
     "주 예수 그리스도의 은혜. NA28 본문에 없음."),
    ("요한일서", 5, 7, 8,
     "Comma Johanneum (요일 5:7b-8a 삼위일체 표현). 후기 라틴 사본에만. NA28 본문에 없음. 학계 다수 후대 첨가."),
]


def flag_textual_critical(
    book_input: str,
    chapter: int,
    verse_start: Optional[int] = None,
    verse_end: Optional[int] = None,
) -> Optional[str]:
    """추천 본문이 사본학적 경계선이면 경고 메시지 반환, 아니면 None."""
    canonical = normalize_book(book_input)
    if not canonical:
        return None
    for b, ch, vs, ve, note in TEXTUAL_CRITICAL_PASSAGES:
        if b != canonical or ch != chapter:
            continue
        target_start = verse_start if verse_start is not None else 1
        target_end = verse_end if verse_end is not None else target_start
        passage_start = vs
        passage_end = ve if ve is not None else vs
        if target_start <= passage_end and target_end >= passage_start:
            ref_str = f"{canonical} {chapter}:{vs}"
            if ve and ve != vs:
                ref_str += f"-{ve}"
            return f"⚠ {ref_str} — {note}"
    return None


# ---------------------------------------------------------------------------
# 6. 메시지 글자 수 검증
# ---------------------------------------------------------------------------
def count_korean_chars(message: str) -> int:
    """전체 문자열 길이 (공백·문장부호 포함). SKILL.md 25-45자 기준."""
    return len(message)


def validate_message_length(message: str, min_chars: int = 25, max_chars: int = 45) -> dict:
    count = count_korean_chars(message)
    if count < min_chars:
        return {
            "ok": False, "count": count,
            "reason": f"메시지가 {count}자로 너무 짧음 ({min_chars}자 이상 권장). 명제가 충분히 드러나는지 점검.",
        }
    if count > max_chars:
        return {
            "ok": False, "count": count,
            "reason": f"메시지가 {count}자로 너무 김 ({max_chars}자 이하 권장). 핵심을 압축.",
        }
    return {"ok": True, "count": count, "reason": None}


# ---------------------------------------------------------------------------
# 7. 5결 매트릭스 패턴 분포 검증
# ---------------------------------------------------------------------------
KEL_DEFINITIONS = {
    1: "신학적 명제",
    2: "실천적 권면",
    3: "내러티브·구속사",
    4: "실존적 진단·답변",
    5: "종말론·소망",
}

PATTERN_DEFINITIONS = {
    "A": [1, 2, 3, 4, 5],
    "B": [1, 1, 2, 4, 5],
    "C": [2, 3, 3, 4, 5],
    "D": [3, 4, 4, 5, 2],
}


def validate_pattern_distribution(kels: list[int], pattern: str = "A") -> dict:
    if len(kels) != 5:
        return {"ok": False, "expected": [], "actual": kels,
                "reason": f"메시지는 정확히 5개여야 합니다 (현재 {len(kels)}개)."}
    for k in kels:
        if k not in KEL_DEFINITIONS:
            return {"ok": False, "expected": [], "actual": kels,
                    "reason": f"잘못된 결 번호 {k}. 1-5만 허용."}
    if pattern not in PATTERN_DEFINITIONS:
        return {"ok": False, "expected": [], "actual": kels,
                "reason": f"잘못된 패턴 '{pattern}'. A/B/C/D만 허용."}
    expected = sorted(PATTERN_DEFINITIONS[pattern])
    actual = sorted(kels)
    if expected != actual:
        return {
            "ok": False,
            "expected": PATTERN_DEFINITIONS[pattern],
            "actual": kels,
            "reason": (
                f"패턴 {pattern} 권장 분포 {PATTERN_DEFINITIONS[pattern]}와 "
                f"실제 분포 {kels}가 일치하지 않습니다. "
                "결을 재배치하거나 다른 패턴을 선택하세요."
            ),
        }
    unique_count = len(set(kels))
    if unique_count < 3:
        return {
            "ok": False,
            "expected": PATTERN_DEFINITIONS[pattern],
            "actual": kels,
            "reason": f"결 다양성 부족 — 유니크 결 {unique_count}개. 최소 3개 결로 분산 권장.",
        }
    return {
        "ok": True,
        "expected": PATTERN_DEFINITIONS[pattern],
        "actual": kels,
        "reason": None,
    }


# ---------------------------------------------------------------------------
# 8. 7가지 작성법 번호 매핑
# ---------------------------------------------------------------------------
SERMON_STYLES = {
    1: ("세 가지 요점 형식", "Three-Point Sermon / Deductive Expository"),
    2: ("내러티브 형식", "Narrative Preaching"),
    3: ("텍스트-주석 형식", "Verse-by-Verse Expository / Lectio Continua"),
    4: ("주제별 형식", "Topical Preaching"),
    5: ("교리 강론 형식", "Doctrinal / Catechetical Preaching"),
    6: ("연극 전달 형식", "Dramatic / First-Person Narrative"),
    7: ("칼빈식 강해 형식", "Calvin-Style Lectio Continua Expository"),
}


def get_sermon_style(number: int) -> Optional[tuple[str, str]]:
    return SERMON_STYLES.get(number)


def list_sermon_styles() -> list[tuple[int, str, str]]:
    return [(n, k, e) for n, (k, e) in sorted(SERMON_STYLES.items())]


# ---------------------------------------------------------------------------
# 9. 데이터 무결성 자체 검증
# ---------------------------------------------------------------------------
EXPECTED_CHAPTER_COUNTS = {
    # 한국 개역개정 4판 / NA28 / BHS 표준 — 66권 전체 장수
    "창세기": 50, "출애굽기": 40, "레위기": 27, "민수기": 36, "신명기": 34,
    "여호수아": 24, "사사기": 21, "룻기": 4,
    "사무엘상": 31, "사무엘하": 24, "열왕기상": 22, "열왕기하": 25,
    "역대상": 29, "역대하": 36, "에스라": 10, "느헤미야": 13, "에스더": 10,
    "욥기": 42, "시편": 150, "잠언": 31, "전도서": 12, "아가": 8,
    "이사야": 66, "예레미야": 52, "예레미야애가": 5, "에스겔": 48, "다니엘": 12,
    "호세아": 14, "요엘": 3, "아모스": 9, "오바댜": 1, "요나": 4, "미가": 7,
    "나훔": 3, "하박국": 3, "스바냐": 3, "학개": 2, "스가랴": 14, "말라기": 4,
    "마태복음": 28, "마가복음": 16, "누가복음": 24, "요한복음": 21, "사도행전": 28,
    "로마서": 16, "고린도전서": 16, "고린도후서": 13, "갈라디아서": 6, "에베소서": 6,
    "빌립보서": 4, "골로새서": 4, "데살로니가전서": 5, "데살로니가후서": 3,
    "디모데전서": 6, "디모데후서": 4, "디도서": 3, "빌레몬서": 1,
    "히브리서": 13, "야고보서": 5, "베드로전서": 5, "베드로후서": 3,
    "요한일서": 5, "요한이서": 1, "요한삼서": 1, "유다서": 1, "요한계시록": 22,
}

# 자주 인용되는 주요 본문의 검증점 (LLM이 자주 혼동하는 본문)
KNOWN_REFERENCES = [
    # (book, chapter, expected_verse_count, source_note)
    ("창세기", 1, 31, "창세기 1장 = 31절 (창조 일곱째 날)"),
    ("창세기", 22, 24, "창세기 22장 = 24절 (이삭 결박)"),
    ("창세기", 50, 26, "창세기 50장 = 26절 (마지막 장)"),
    ("출애굽기", 20, 26, "출 20장 = 26절 (십계명 + 단 규정)"),
    ("레위기", 19, 37, "레 19장 = 37절"),
    ("신명기", 6, 25, "신 6장 = 25절 (쉐마)"),
    ("시편", 1, 6, "시 1편 = 6절"),
    ("시편", 22, 31, "시 22편 = 31절 (메시아 시편)"),
    ("시편", 23, 6, "시 23편 = 6절 (목자 시)"),
    ("시편", 51, 19, "시 51편 = 19절 (다윗 회개시)"),
    ("시편", 119, 176, "시 119편 = 176절 (가장 긴 시편)"),
    ("잠언", 31, 31, "잠 31장 = 31절 (현숙한 여인)"),
    ("이사야", 6, 13, "사 6장 = 13절 (이사야 부르심)"),
    ("이사야", 53, 12, "사 53장 = 12절 (고난 받는 종)"),
    ("예레미야", 29, 32, "렘 29장 = 32절 (포로기 위로)"),
    ("다니엘", 6, 28, "단 6장 = 28절 (사자굴)"),
    ("요나", 3, 10, "욘 3장 = 10절"),
    ("마태복음", 5, 48, "마 5장 = 48절 (산상수훈 시작)"),
    ("마태복음", 28, 20, "마 28장 = 20절 (대위임령)"),
    ("마가복음", 16, 20, "막 16장 = 20절 (긴 결말 포함)"),
    ("누가복음", 15, 32, "눅 15장 = 32절 (잃은 자 비유)"),
    ("요한복음", 3, 36, "요 3장 = 36절 (니고데모, 요 3:16)"),
    ("요한복음", 14, 31, "요 14장 = 31절"),
    ("요한복음", 21, 25, "요 21장 = 25절 (마지막 장)"),
    ("사도행전", 2, 47, "행 2장 = 47절 (오순절)"),
    ("로마서", 8, 39, "롬 8장 = 39절"),
    ("로마서", 12, 21, "롬 12장 = 21절"),
    ("고린도전서", 13, 13, "고전 13장 = 13절 (사랑 장)"),
    ("고린도전서", 15, 58, "고전 15장 = 58절 (부활 장)"),
    ("갈라디아서", 5, 26, "갈 5장 = 26절 (성령의 열매)"),
    ("에베소서", 4, 32, "엡 4장 = 32절"),
    ("에베소서", 6, 24, "엡 6장 = 24절"),
    ("빌립보서", 4, 23, "빌 4장 = 23절"),
    ("히브리서", 11, 40, "히 11장 = 40절 (믿음 장)"),
    ("히브리서", 12, 29, "히 12장 = 29절"),
    ("야고보서", 1, 27, "약 1장 = 27절"),
    ("베드로전서", 5, 14, "벧전 5장 = 14절"),
    ("요한일서", 4, 21, "요일 4장 = 21절"),
    ("요한일서", 5, 21, "요일 5장 = 21절"),
    ("요한계시록", 21, 27, "계 21장 = 27절 (새 하늘 새 땅)"),
    ("요한계시록", 22, 21, "계 22장 = 21절 (성경 마지막)"),
]


def self_check() -> dict:
    """모듈 자체 무결성 검증.

    반환: {ok: bool, errors: list[str]}
    """
    errors: list[str] = []

    # 1) 66권 누락 검사
    for book in OT_BOOKS_ORDERED + NT_BOOKS_ORDERED:
        if book not in CHAPTER_VERSES:
            errors.append(f"CHAPTER_VERSES에 누락: {book}")

    # 2) 책당 장수가 표준값과 일치
    for book, expected in EXPECTED_CHAPTER_COUNTS.items():
        chapters = CHAPTER_VERSES.get(book)
        if not chapters:
            continue
        actual = len(chapters)
        if actual != expected:
            errors.append(
                f"장수 불일치: {book} (표준 {expected}장, 데이터 {actual}장)"
            )

    # 3) 알려진 본문 검증점 확인
    for book, chapter, expected_verses, note in KNOWN_REFERENCES:
        chapters = CHAPTER_VERSES.get(book)
        if not chapters:
            errors.append(f"검증점 책 없음: {note}")
            continue
        if chapter > len(chapters):
            errors.append(f"검증점 장 없음: {note} (책 총 {len(chapters)}장)")
            continue
        actual = chapters[chapter - 1]
        if actual != expected_verses:
            errors.append(
                f"검증점 절수 불일치: {note} — 데이터 {actual}절"
            )

    # 4) 약어 사전이 정식 책명을 모두 가리키는지
    for abbr, full in BOOK_ABBR_KO.items():
        if full not in ALL_BOOKS:
            errors.append(f"약어 사전 잘못된 매핑: '{abbr}' → '{full}' (정경 외)")

    # 5) 패턴 정의 검증
    for pattern, dist in PATTERN_DEFINITIONS.items():
        if len(dist) != 5:
            errors.append(f"패턴 '{pattern}' 분포가 5개가 아님: {dist}")
        for k in dist:
            if k not in KEL_DEFINITIONS:
                errors.append(f"패턴 '{pattern}'에 잘못된 결 번호: {k}")

    # 6) 사본학 경계선 본문이 실제 정경 안에 있는지
    for book, chapter, vs, ve, note in TEXTUAL_CRITICAL_PASSAGES:
        chapters = CHAPTER_VERSES.get(book)
        if not chapters:
            errors.append(f"경계선 본문의 책이 없음: {book}")
            continue
        if chapter > len(chapters):
            errors.append(f"경계선 본문의 장 없음: {book} {chapter}장")

    return {"ok": len(errors) == 0, "errors": errors}


# ---------------------------------------------------------------------------
# 10. CLI 진입점
# ---------------------------------------------------------------------------
def _cli():
    """간단 CLI 도구

    명령:
        ref <book> <chapter> [verse_start] [verse_end]
        balance <ref1> <ref2> ... (각 ref는 'book:chap:vs:ve' 형식)
        flag <book> <chapter> <verse_start> [verse_end]
        len <message>
        pattern <pattern_letter> <k1,k2,k3,k4,k5>
        style <number>
        styles
        selfcheck
    """
    import sys
    args = sys.argv[1:]
    if not args:
        print(_cli.__doc__)
        return
    cmd = args[0]
    if cmd == "ref":
        b = args[1]
        c = int(args[2])
        vs = int(args[3]) if len(args) > 3 else None
        ve = int(args[4]) if len(args) > 4 else None
        print(validate_reference(b, c, vs, ve))
    elif cmd == "balance":
        refs = []
        for r in args[1:]:
            parts = r.split(":")
            book = parts[0]
            chap = int(parts[1])
            vs = int(parts[2]) if len(parts) > 2 and parts[2] else None
            ve = int(parts[3]) if len(parts) > 3 and parts[3] else None
            refs.append((book, chap, vs, ve))
        print(check_balance(refs))
    elif cmd == "flag":
        b = args[1]
        c = int(args[2])
        vs = int(args[3])
        ve = int(args[4]) if len(args) > 4 else None
        result = flag_textual_critical(b, c, vs, ve)
        print(result if result else "(no flag — 사본학 이슈 없음)")
    elif cmd == "len":
        m = " ".join(args[1:])
        print(validate_message_length(m))
    elif cmd == "pattern":
        p = args[1].upper()
        ks = [int(x) for x in args[2].split(",")]
        print(validate_pattern_distribution(ks, p))
    elif cmd == "style":
        n = int(args[1])
        print(get_sermon_style(n))
    elif cmd == "styles":
        for n, ko, en in list_sermon_styles():
            print(f"{n}: {ko} ({en})")
    elif cmd == "selfcheck":
        result = self_check()
        if result["ok"]:
            print("PASS — 데이터 무결성 검증 통과")
        else:
            print("FAIL — 다음 오류 발견:")
            for e in result["errors"]:
                print(f"  - {e}")
    else:
        print(f"Unknown command: {cmd}")
        print(_cli.__doc__)


if __name__ == "__main__":
    _cli()
