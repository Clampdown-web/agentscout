#!/usr/bin/env python3
"""Apply the growth build. Run from the repo root: python3 scripts/apply_growth.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_growth

if __name__ == "__main__":
    build_growth.main()
