#!/usr/bin/env bash
# One-click launcher for Linux / macOS
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install PySide6 matplotlib
python main.py
