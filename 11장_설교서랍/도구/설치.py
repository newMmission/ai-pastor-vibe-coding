# -*- coding: utf-8 -*-
"""설교서랍 설치 — 설치.bat 이 부릅니다.

1) 화면에 필요한 flask 를 설치하고
2) 바탕화면에 [설교서랍] 아이콘(바로가기)을 만듭니다.
Copyright (c) 2026 newMmission (뉴엠미션, 쟈니파커) — MIT License
"""
import base64
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def install_flask():
    try:
        import flask  # noqa: F401
        print("  flask: 이미 있습니다.")
    except ImportError:
        print("  flask를 설치합니다. 1~2분 걸릴 수 있습니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(BASE / "requirements.txt")])


def make_shortcut():
    # 한글 경로가 깨지지 않도록 PowerShell 명령을 UTF-16으로 감싸서 보낸다
    ps = f"""
$desk = [Environment]::GetFolderPath('Desktop')
$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desk '설교서랍.lnk'))
$s.TargetPath = '{BASE / "실행.bat"}'
$s.WorkingDirectory = '{BASE}'
$s.IconLocation = '{BASE / "설교서랍.ico"}'
$s.WindowStyle = 7
$s.Description = '설교서랍 — AI 목회자 바이브 코딩 11장'
$s.Save()
Write-Output (Join-Path $desk '설교서랍.lnk')
"""
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    out = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", enc],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        print("  아이콘을 만들지 못했습니다:", out.stderr.strip())
        return False
    print("  바탕화면 아이콘:", out.stdout.strip())
    return True


if __name__ == "__main__":
    print("[1/2] 화면 준비")
    install_flask()
    print("[2/2] 바탕화면 아이콘 만들기")
    ok = make_shortcut()
    print()
    print("다 되었습니다. 바탕화면의 [설교서랍] 아이콘을 두 번 누르세요." if ok
          else "아이콘은 만들지 못했지만, 이 폴더의 실행.bat 을 두 번 누르면 열립니다.")
