# -*- coding: utf-8 -*-
"""설교서랍 화면 — 기쁨교회 박목사의 설교 도우미 (11장 예제)

이 화면에는 AI가 들어 있지 않습니다. 글을 쓰고 고치는 일은 Cursor의 AI가 `설교서랍.md`(방법서)대로 합니다.
이 화면은 ① 초안을 넣고 ② 설교본을 읽고 연습하며 @@ 표시를 하고 ③ 장절을 검증하고 ④ 완성본을 정하는 곳입니다.

실행: 실행.bat 을 두 번 누르거나,  py app.py  →  http://127.0.0.1:5050
Copyright (c) 2026 newMmission (뉴엠미션, 쟈니파커) — MIT License
"""
import difflib
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import webbrowser
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

BASE = Path(__file__).resolve().parent
DRAFTS = BASE / "초안"
SERMONS = BASE / "설교"
for d in (DRAFTS, SERMONS, BASE / "메모서랍"):
    d.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE / "도구"))
import 장절검사  # noqa: E402

PORT = 5050
CHARS_PER_MINUTE = 270  # 소리 내어 읽을 때 1분에 읽는 글자 수(공백 제외) 어림
app = Flask(__name__)


# ---------- 파일 도우미 ----------

def next_sunday():
    t = date.today()
    return (t + timedelta(days=(6 - t.weekday()) % 7)).isoformat()


def numbered(folder, stem):
    """stem_v01.md, stem_v02.md … 를 번호 순서로"""
    if not folder.exists():
        return []
    files = [p for p in folder.glob(f"{stem}_v*.md") if re.search(r"_v(\d+)$", p.stem)]
    return sorted(files, key=lambda p: int(re.search(r"_v(\d+)$", p.stem).group(1)))


def save_next(folder, stem, text):
    folder.mkdir(parents=True, exist_ok=True)
    n = len(numbered(folder, stem)) + 1
    path = folder / f"{stem}_v{n:02d}.md"
    path.write_text(text, encoding="utf-8")  # 언제나 새 번호 — 옛 판은 덮어쓰지 않는다
    return path


def sermon_folder(day):
    return SERMONS / f"{day}_주일설교"


def all_days():
    days = {p.name.split("_")[0] for p in DRAFTS.glob("*.md")}
    days |= {p.name.split("_")[0] for p in SERMONS.iterdir() if p.is_dir()}
    return sorted(d for d in days if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))


def stamp_of(p):
    """파일 이름 + 고친 시각 — AI가 같은 파일을 고쳐 써도 화면이 알아챈다"""
    return f"{p.name}:{p.stat().st_mtime_ns}"


def read(p):
    return p.read_text(encoding="utf-8") if p and p.exists() else ""


def minutes(text):
    n = len(re.sub(r"\s", "", text))
    return n, round(n / CHARS_PER_MINUTE)


# ---------- 화면 ----------

PAGE = r"""
<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>설교서랍</title>
<style>
 body{font-family:'맑은 고딕',sans-serif;font-size:19px;color:#000;background:#fff;max-width:1000px;margin:20px auto;padding:0 16px}
 h1{font-size:30px;margin:6px 0} h2{font-size:23px;margin:0 0 10px}
 .box{border:3px solid #000;border-radius:12px;padding:16px 20px;margin:18px 0}
 .say{border:2px dashed #000;background:#f2f2f2;padding:8px 12px;margin:8px 0;font-weight:bold}
 .say button{font-size:15px;margin-left:10px;padding:2px 10px}
 textarea{width:100%;box-sizing:border-box;font-size:18px;line-height:1.7;padding:10px;font-family:inherit}
 #sermon{font-size:var(--fs,22px);line-height:1.9}
 button,input,select{font-size:18px} button{padding:6px 18px;border:2px solid #000;border-radius:8px;background:#e6e6e6;cursor:pointer;margin:4px 2px}
 table{border-collapse:collapse;width:100%} td,th{border:1px solid #000;padding:6px;font-size:17px;vertical-align:top} th{background:#d9d9d9}
 .muted{color:#555;font-size:16px} .bad{font-weight:bold;text-decoration:underline}
 .add{font-weight:bold} .del{text-decoration:line-through;color:#666}
 .banner{border:3px solid #000;background:#d9d9d9;padding:10px;font-weight:bold;display:none}
</style></head><body>
<h1>📖 설교서랍</h1>
<form method="post" action="{{ url_for('open_cursor') }}" style="margin:6px 0">
 <button>🖥 Cursor로 열기</button> <span class="muted">이 설교서랍 폴더를 Cursor에서 엽니다. 오른쪽 대화창에 말하시면 됩니다.</span></form>
{% if message %}<div class="say">{{ message }}</div>{% endif %}
<p class="muted">AI는 펼쳐 보이고, 목사는 기도하며 고릅니다. 글을 쓰고 고치는 일은 <b>Cursor 대화창</b>에 말하면 됩니다.</p>

<form method="get">주일 날짜
 <input name="d" value="{{ day }}" size="11">
 {% for x in days %}<a href="?d={{ x }}">{{ x }}</a> {% endfor %}
 <button>열기</button></form>

<div class="box">
 <h2>① 메모 · 주제 · 초안 — Cursor에 말하기</h2>
 <div class="say">메모 정리해 줘요 <button onclick="cp(this)">복사</button></div>
 <div class="say">{{ day }} 주일 설교 주제 만들어 줘요 <button onclick="cp(this)">복사</button></div>
 <div class="say">주제 1번으로 초안 만들어 줘요 <button onclick="cp(this)">복사</button></div>
 {% if topics %}<details><summary>주제 다섯 개 보기 (1_주제.md)</summary><pre style="white-space:pre-wrap">{{ topics }}</pre></details>{% endif %}
 {% if mindmap %}<details><summary>마인드맵 보기 (2_마인드맵.md)</summary><pre style="white-space:pre-wrap">{{ mindmap }}</pre></details>{% endif %}
 {% if candidates %}<details><summary>초안 후보 보기 ({{ day }}_초안후보.md)</summary><pre style="white-space:pre-wrap">{{ candidates }}</pre></details>{% endif %}
</div>

<div class="box">
 <h2>② 초안 넣기</h2>
 <p class="muted">골방에서 고른 초안을 붙여 넣으세요. AI가 만든 초안이든, 목사님이 쓰신 초안이든 됩니다. 결론을 어느 쪽으로 맺고 싶으신지도 한두 줄 적어 주세요.</p>
 <form method="post" action="{{ url_for('save_draft', d=day) }}">
  <textarea name="draft" rows="9">{{ draft }}</textarea>
  <button>초안 저장</button> {% if draft_file %}<span class="muted">지금 초안: {{ draft_file }}</span>{% endif %}
 </form>
 <div class="say">설교본 만들어 줘요 <button onclick="cp(this)">복사</button></div>
</div>

<div class="box">
 <h2>③ 설교본 — 읽고, 또 읽고, 연습하며 @@ 표시</h2>
 <div class="banner" id="banner">새 판이 도착했습니다. <button onclick="location.reload()">새로 보기</button></div>
 {% if sermon_file %}
 <p><b>{{ sermon_file }}</b> · 공백 빼고 {{ chars }}자 · 소리 내어 읽으면 약 <b>{{ mins }}분</b>
  {% if marks %} · <span class="bad">@@ {{ marks }}곳</span>{% endif %}
  · 글씨 <button onclick="fs(2)">크게</button><button onclick="fs(-2)">작게</button></p>
 <p class="muted">고칠 자리 바로 뒤에 <b>@@ 고칠 말</b>을 적으세요. 예) …버려져 있었습니다. @@ 짧게 줄여라</p>
 <form method="post" action="{{ url_for('save_marks', d=day) }}">
  <textarea id="sermon" name="text" rows="24" oninput="dirty=true">{{ sermon }}</textarea>
  <button>@@ 표시 저장 (새 번호로)</button>
 </form>
 <div class="say">@@ 표시대로 고쳐 줘요 <button onclick="cp(this)">복사</button></div>
 <p>판 보기: {% for v in versions %}<a href="?d={{ day }}&v={{ v }}">{{ v }}</a> {% endfor %}</p>
 <form method="get">판 비교 <input type="hidden" name="d" value="{{ day }}">
  <select name="a">{% for v in versions %}<option {{ 'selected' if loop.index==versions|length-1 }}>{{ v }}</option>{% endfor %}</select> →
  <select name="b">{% for v in versions %}<option {{ 'selected' if loop.last }}>{{ v }}</option>{% endfor %}</select>
  <button formaction="{{ url_for('compare') }}">무엇이 바뀌었나</button></form>
 {% else %}<p class="muted">아직 설교본이 없습니다. 초안을 넣고 Cursor에 "설교본 만들어 줘요"라고 말하세요.</p>{% endif %}
</div>

<div class="box">
 <h2>④ 성경 장절 확인 <span class="muted">(설교본에 적힌 "에스겔 16:6" 같은 장·절이 성경에 실제로 있는지 컴퓨터가 확인합니다. AI가 아닙니다)</span></h2>
 <form method="post" action="{{ url_for('check', d=day) }}"><button>성경 장절 확인</button></form>
 {% if checked is not none %}
  {% if checked %}<table><tr><th>본문에 적힌 대로</th><th>결과</th><th>까닭</th><th>사본학 주의</th></tr>
  {% for r in checked %}<tr><td>{{ r['본문에 적힌 대로'] }}</td><td class="{{ 'bad' if r['결과']=='틀림' }}">{{ r['결과'] }}</td><td>{{ r['까닭'] }}</td><td>{{ r['사본학 주의'] }}</td></tr>{% endfor %}</table>
  <p class="muted">"맞음"은 그 장·절이 성경에 있다는 뜻입니다. 인용한 말씀의 글자가 맞는지는 성경을 펴서 직접 대조하세요.</p>
  {% else %}<p>설교본에서 장절을 찾지 못했습니다.</p>{% endif %}
 {% endif %}
</div>

<div class="box">
 <h2>⑤ 완성본</h2>
 <form method="post" action="{{ url_for('finish', d=day) }}"><button>✔ 완성본으로 정하기</button></form>
 {% if final %}<p>완성본: <b>{{ final }}</b></p>{% endif %}
</div>
<p class="muted">MIT License · 자세한 내용은 LICENSE.md</p>

<script>
 var dirty=false, shown="{{ stamp }}";
 function cp(b){navigator.clipboard.writeText(b.parentNode.firstChild.textContent.trim());b.textContent='복사됨';}
 function fs(n){var e=document.getElementById('sermon');if(!e)return;var s=parseInt(getComputedStyle(e).fontSize)+n;e.style.setProperty('--fs',s+'px');}
 {% if not viewing_old %}
 setInterval(function(){fetch('{{ url_for("latest", d=day) }}').then(r=>r.json()).then(j=>{
   if(j.latest && j.latest!==shown){ if(dirty){document.getElementById('banner').style.display='block';} else {location.reload();} }
 });},4000);
 {% endif %}
</script>
</body></html>
"""

COMPARE = r"""
<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>판 비교</title>
<style>body{font-family:'맑은 고딕',sans-serif;font-size:19px;max-width:1000px;margin:20px auto;padding:0 16px;line-height:1.8}
.add{font-weight:bold;border-left:6px solid #000;padding-left:8px}.del{text-decoration:line-through;color:#666;border-left:6px dotted #999;padding-left:8px}</style></head><body>
<h2>{{ a }} → {{ b }} : 무엇이 바뀌었나</h2>
<p>굵은 글씨 = 새로 들어간 줄 · <span class="del">줄 그은 글씨</span> = 빠진 줄</p>
{% for kind, line in rows %}<div class="{{ kind }}">{{ line }}</div>{% else %}<p>바뀐 곳이 없습니다.</p>{% endfor %}
<p><a href="{{ back }}">← 돌아가기</a></p></body></html>
"""

_checked = {}


@app.get("/")
def home():
    day = request.args.get("d") or (all_days()[-1] if all_days() else next_sunday())
    folder = sermon_folder(day)
    drafts = numbered(DRAFTS, f"{day}_초안")
    sermons = numbered(folder, "설교본")
    pick = request.args.get("v")
    current = next((p for p in sermons if p.stem.endswith(pick or "")), None) if pick else (sermons[-1] if sermons else None)
    text = read(current)
    chars, mins = minutes(text)
    finals = sorted(folder.glob("완성본*.md")) if folder.exists() else []
    return render_template_string(
        PAGE, url_for=url_for, day=day, days=all_days(),
        topics=read(folder / "1_주제.md"), mindmap=read(folder / "2_마인드맵.md"), candidates=read(DRAFTS / f"{day}_초안후보.md"),
        draft=read(drafts[-1]) if drafts else "", draft_file=drafts[-1].name if drafts else "",
        sermon=text, sermon_file=current.name if current else "", chars=chars, mins=mins,
        stamp=stamp_of(sermons[-1]) if sermons else "",
        marks=text.count("@@"), versions=[p.stem.split("_")[-1] for p in sermons],
        viewing_old=bool(pick and sermons and current != sermons[-1]),
        checked=_checked.pop(day, None), message=request.args.get("msg", ""),
        final=finals[-1].name if finals else "")


@app.post("/draft")
def save_draft():
    day = request.args["d"]
    text = request.form.get("draft", "").strip()
    if text:
        save_next(DRAFTS, f"{day}_초안", text)
    return redirect(url_for("home", d=day))


@app.post("/marks")
def save_marks():
    day = request.args["d"]
    text = request.form.get("text", "").replace("\r\n", "\n")
    if text.strip():
        save_next(sermon_folder(day), "설교본", text)
    return redirect(url_for("home", d=day))


@app.get("/latest")
def latest():
    sermons = numbered(sermon_folder(request.args["d"]), "설교본")
    return jsonify(latest=stamp_of(sermons[-1]) if sermons else "")


@app.post("/check")
def check():
    day = request.args["d"]
    sermons = numbered(sermon_folder(day), "설교본")
    _checked[day] = 장절검사.check_text(read(sermons[-1])) if sermons else []
    return redirect(url_for("home", d=day))


@app.get("/compare")
def compare():
    day, a, b = request.args["d"], request.args["a"], request.args["b"]
    folder = sermon_folder(day)
    ta, tb = read(folder / f"설교본_{a}.md"), read(folder / f"설교본_{b}.md")
    rows = []
    for line in difflib.ndiff(ta.splitlines(), tb.splitlines()):
        if line.startswith("+ ") and line[2:].strip():
            rows.append(("add", line[2:]))
        elif line.startswith("- ") and line[2:].strip():
            rows.append(("del", line[2:]))
    return render_template_string(COMPARE, a=a, b=b, rows=rows, back=url_for("home", d=day))


@app.post("/finish")
def finish():
    day = request.args["d"]
    folder = sermon_folder(day)
    sermons = numbered(folder, "설교본")
    if not sermons:
        return redirect(url_for("home", d=day, msg="아직 설교본이 없습니다."))
    text = read(sermons[-1])
    if "@@" in text:
        return redirect(url_for("home", d=day, msg=f"@@ 표시가 {text.count('@@')}곳 남아 있습니다. 먼저 고쳐 주세요."))
    text = text.replace("[초안]", "").strip() + "\n"
    n = len(list(folder.glob("완성본*.md"))) + 1
    name = "완성본.md" if n == 1 else f"완성본_v{n:02d}.md"
    (folder / name).write_text(text, encoding="utf-8")
    return redirect(url_for("home", d=day, msg=f"{name}으로 정했습니다."))


def find_cursor():
    """Cursor 프로그램 찾기 — 보통 설치되는 자리를 먼저 보고, 없으면 cursor 명령어를 찾는다"""
    exe = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "cursor" / "Cursor.exe"
    if exe.exists():
        return [str(exe)], False
    found = shutil.which("cursor")
    return ([found], True) if found else (None, False)


@app.post("/cursor")
def open_cursor():
    cmd, use_shell = find_cursor()
    if not cmd:
        return redirect(url_for("home", msg="Cursor를 찾지 못했습니다. cursor.com에서 Cursor를 먼저 설치해 주세요."))
    subprocess.Popen(cmd + [str(BASE)], shell=use_shell)
    return redirect(url_for("home", msg="Cursor를 열었습니다. 오른쪽 대화창에 말해 보세요."))


def already_running():
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", PORT)) == 0


if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    if already_running():  # 아이콘을 두 번 눌렀을 때 — 이미 켜져 있으면 화면만 다시 연다
        webbrowser.open(url)
        sys.exit(0)
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(port=PORT, debug=False)
