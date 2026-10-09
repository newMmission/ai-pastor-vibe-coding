@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 설교서랍 - 이 창을 닫으면 설교서랍이 꺼집니다
set PY=
where py >nul 2>&1 && set PY=py
if not defined PY ( where python >nul 2>&1 && set PY=python )
if not defined PY (
  echo 파이썬이 없습니다. 먼저 설치.bat 을 두 번 눌러 주십시오.
  pause
  exit /b
)
echo 설교서랍을 엽니다. 잠시 뒤 인터넷 창에 화면이 뜹니다.
echo 이 까만 창은 작게 내려 두십시오. 닫으면 설교서랍이 꺼집니다.
%PY% -c "import flask" >nul 2>&1 || %PY% -m pip install -r requirements.txt
%PY% app.py
