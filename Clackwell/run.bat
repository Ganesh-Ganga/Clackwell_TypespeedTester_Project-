@echo off
REM One-shot setup + start for Windows.
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
python app.py
