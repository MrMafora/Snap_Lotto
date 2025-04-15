"""
This is a minimal Flask application that runs on port 8080.
"""
from flask import Flask, redirect, url_for

app = Flask(__name__)

# Create a simple redirect endpoint
@app.route('/')
def home():
    return redirect('https://45399ea3-630c-4463-8e3d-edea73bb30a7-00-12l5s06oprbcf.janeway.replit.dev:5000/')

@app.route('/health')
def health():
    return 'OK'

# Directly run the application on port 8080
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)