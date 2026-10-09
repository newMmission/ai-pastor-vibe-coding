@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   설교서랍 설치 (처음 한 번만 하시면 됩니다)
echo ================================================
echo.
set PY=
where py >nul 2>&1 && set PY=py
if not defined PY ( where python >nul 2>&1 && python --version >nul 2>&1 && set PY=python )
if not defined PY (
  echo 파이썬이 아직 없습니다.
  echo 책 11장의 "파이썬 설치하기"를 따라 파이썬을 먼저 설치해 주십시오.
  echo 설치할 때 "Add python.exe to PATH" 칸에 꼭 체크하십시오.
  echo.
  echo 파이썬 내려받는 곳을 열어 드립니다...
  start https://www.python.org/downloads/
  echo.
  pause
  exit /b
)
%PY% 도구\설치.py
echo.
pause
