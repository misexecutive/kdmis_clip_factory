@echo off
setlocal enabledelayedexpansion
title Nyro AI Clip Factory - Gamer Nyro
color 0b
cls

echo =====================================================================
echo                NYRO AI CLIP FACTORY - GAMER NYRO                     
echo           Local AI Gaming Video Automation and Shorts Studio         
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python runtime...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH!
    echo Please ensure Python 3.10+ is installed and added to Windows PATH.
    pause
    exit /b 1
)

echo [2/3] Checking storage directories...
if not exist "storage\raw_recordings" mkdir "storage\raw_recordings"
if not exist "storage\exports" mkdir "storage\exports"
if not exist "storage\cache" mkdir "storage\cache"
if not exist "storage\sfx" mkdir "storage\sfx"

echo [3/3] Ready!
echo.
echo =====================================================================
echo  Select Operation Mode:
echo    [1] Interactive Studio Dashboard (Loads latest video in browser)
echo    [2] Fresh Start Dashboard (Wipes old test runs and loads clean)
echo    [3] Autonomous Zero-Touch Director (Auto-renders Top 3 Shorts)
echo    [4] Reset Database and Cache Only
echo =====================================================================
echo.

choice /c 1234 /n /m "Press [1, 2, 3, or 4]: "
set "user_choice=%errorlevel%"

if "%user_choice%"=="4" goto do_reset
if "%user_choice%"=="3" goto do_auto
if "%user_choice%"=="2" goto do_fresh
if "%user_choice%"=="1" goto do_start
goto do_start

:do_start
echo.
echo [Clip Factory] Launching Interactive Studio Dashboard...
python run_clip_factory.py start --port 8000
goto finished

:do_fresh
echo.
echo [Clip Factory] Starting FRESH Studio Dashboard (clearing past sessions)...
python run_clip_factory.py start --fresh --port 8000
goto finished

:do_auto
echo.
echo [Clip Factory] Starting Autonomous Zero-Touch Production...
echo [Clip Factory] Inspecting video, color grading, adding SFX, and rendering...
python run_clip_factory.py auto --top 3
echo.
echo =====================================================================
echo Production Complete! Check storage\exports\ for your rendered Shorts!
echo =====================================================================
pause
goto finished

:do_reset
echo.
echo [Clip Factory] Purging database and cache...
python run_clip_factory.py reset
echo.
echo Database and cache have been wiped clean.
pause
goto finished

:finished
if errorlevel 1 (
    echo.
    echo [ERROR] Process exited with code %errorlevel%.
    pause
)
