#!/bin/bash
csv_file=~/Downloads/supabase_aouvjyxihpudhbmbuepk_shuttle\ progress\ graph\ data.csv 
cp $csv_file data.csv
rm $csv_file
. venv/bin/activate
python3 parse.py
