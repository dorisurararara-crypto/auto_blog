@echo off
cd /d C:\auto_blog
echo [%date% %time%] 자동 포스팅 작업을 시작합니다... >> 자동실행_로그.txt

rem 1. 최신 상태 유지를 위해 깃 풀 (필요 시)
git pull origin main >> 자동실행_로그.txt 2>&1

rem 2. 가상환경이 있다면 활성화 (현재 .venv 폴더가 보입니다)
call .venv\Scripts\activate >> 자동실행_로그.txt 2>&1

rem 3. 메인 스크립트 실행
py manager.py >> 자동실행_로그.txt 2>&1

echo [%date% %time%] 작업이 완료되었습니다. >> 자동실행_로그.txt
echo ------------------------------------------ >> 자동실행_로그.txt
deactivate
