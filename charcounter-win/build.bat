@echo off
chcp 65001 >nul
pip install pyinstaller -r requirements.txt
pyinstaller --onefile --windowed --name "Character Counter" app.py
echo.
echo 완료! dist 폴더의 Character Counter.exe 를 쓰면 돼요.
pause
