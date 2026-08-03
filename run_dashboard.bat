@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Membuat virtual environment...
    py -3.13 -m venv .venv
    if errorlevel 1 (
        py -3.12 -m venv .venv
    )
    if errorlevel 1 (
        echo.
        echo Python 3.12 atau 3.13 tidak ditemukan.
        echo Python 3.14 belum didukung oleh paket dashboard ini.
        pause
        exit /b 1
    )
)

echo [2/3] Memasang atau memeriksa library...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    echo.
    echo Instalasi gagal. Pastikan internet aktif dan Python sudah terpasang.
    pause
    exit /b 1
)

echo [3/3] Membuka dashboard...
".venv\Scripts\python.exe" -m streamlit run app.py

pause
