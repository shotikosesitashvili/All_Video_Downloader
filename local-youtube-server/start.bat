@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo პაკეტების დაყენება ვერ მოხერხდა.
  echo გადაამოწმე Python-ის დაყენება და ინტერნეტკავშირი.
  pause
  exit /b 1
)
python app.py
pause

