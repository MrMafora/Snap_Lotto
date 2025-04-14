"""
Direct port 8080 implementation of main application.
This file is identical to main.py except it binds to port 8080.
"""
import os
import sys
import logging
import threading
import flask
import flask_login
import flask_wtf.csrf
import werkzeug.middleware.proxy_fix
import werkzeug.security
import werkzeug.utils
import time
import json
import uuid
import re
import datetime
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Import the original app and models from main.py to avoid duplication
from main import app, init_database, init_lazy_modules, LotteryResult, User, Screenshot

if __name__ == "__main__":
    # Initialize database in a separate thread
    db_thread = threading.Thread(target=init_database)
    db_thread.daemon = True
    db_thread.start()
    
    # Initialize modules in a separate thread
    init_thread = threading.Thread(target=init_lazy_modules)
    init_thread.daemon = True
    init_thread.start()
    
    print("Starting application on port 8080...")
    app.run(host="0.0.0.0", port=8080, debug=True)