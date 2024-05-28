#!/bin/bash
cp ~/Downloads/supabase_aouvjyxihpudhbmbuepk_shuttle\ progress\ graph\ data.csv data.csv
. venv/bin/activate
python3 parse.py
