#!/usr/bin/env bash
# One-shot setup + start for macOS/Linux.
set -e
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
