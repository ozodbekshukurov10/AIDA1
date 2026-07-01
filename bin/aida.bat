@echo off
REM AIDA Beta — CLI entry point (Windows)
REM Usage: aida [prompt] [--read FILE] [--run CMD] [--mode plan|auto|approve]
python "%~dp0..\aida_beta\cli.py" %*
