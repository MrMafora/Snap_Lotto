#!/bin/bash
# Environment variables for deployment
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export FLASK_ENV=production