@echo off
start http://localhost:8501
.\.venv\Scripts\python.exe -m streamlit run avaliacao/avaliacao.py
pause