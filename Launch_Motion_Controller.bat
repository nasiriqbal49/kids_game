@echo off
title Universal Motion Controller
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python tools/motion_controller_app.py