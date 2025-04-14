"""
A simple Flask application to test Replit deployment.
This is based on the recommendations from Replit support.
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'App is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)