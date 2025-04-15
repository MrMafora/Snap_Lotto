#!/bin/bash

# Start the application on port 8080
exec gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app