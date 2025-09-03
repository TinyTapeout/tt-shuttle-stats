#!/bin/bash
csv_file=~/Downloads/Supabase\ Snippet\ shuttle\ progress\ graph.csv
cp "$csv_file" data.csv
rm "$csv_file"
. venv/bin/activate
python3 parse.py
