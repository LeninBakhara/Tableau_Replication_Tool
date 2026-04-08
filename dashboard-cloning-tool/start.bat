@echo off
echo ==================================
echo  Dashboard Cloning Tool
echo  by Decision Tree
echo ==================================
echo.
cd /d "%~dp0backend"
echo Checking dependencies...
pip install -r requirements.txt -q
echo.
echo Starting server...
echo Open http://localhost:8000 in your browser
echo.
echo Login: lenin.bakhara@decision-tree.com
echo Password: Admin@1234
echo.
echo Press Ctrl+C to stop
echo ----------------------------------
python main.py
pause
