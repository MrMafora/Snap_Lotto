"""
Simple standalone server to demonstrate the ticket scanner interface.
"""
from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def home():
    try:
        return send_file('scanner_demo.html')
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("Starting demo server on port 8080...")
    app.run(host="0.0.0.0", port=8080)