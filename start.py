#!/usr/bin/env python3
"""
start.py - Wrapper per avviare uvicorn con PORT da variabile d'ambiente
"""
import os
import sys

if __name__ == "__main__":
    port = os.getenv("PORT", "8000")
    os.execvp("uvicorn", [
        "uvicorn",
        "api:app",
        "--host", "0.0.0.0",
        "--port", port,
    ])
