#!/bin/bash

# First run the pre-start script to open port 5000 quickly
echo "Running pre-start..."
python pre_start.py

# Then start gunicorn (this will become the foreground process)
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app