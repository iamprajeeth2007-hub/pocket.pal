@echo off
REM Create Windows-native virtual environment and install dependencies
python -m venv backend\\venv-windows
call backend\\venv-windows\\Scripts\\activate.bat
pip install --upgrade pip
pip install -r backend\\requirements.txt
echo Dependencies installed. Use "backend\\venv-windows\\Scripts\\activate.bat" to activate.
