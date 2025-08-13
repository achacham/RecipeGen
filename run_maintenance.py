#!/usr/bin/env python
"""
Simple runner for database maintenance
Run from main project folder: python run_maintenance.py
"""

from db_maintenance.daily_maintenance import run_complete_maintenance

if __name__ == "__main__":
    run_complete_maintenance()