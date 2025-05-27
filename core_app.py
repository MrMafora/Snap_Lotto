"""
Clean, standardized Flask application for Snap Lotto
Following Flask best practices with proper separation of concerns
"""
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.utils import secure_filename
import anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'lottery-default-secret')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lottery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Initialize database
db = SQLAlchemy(app)

# Database Models
class LotteryResult(db.Model):
    __tablename__ = 'lottery_result'
    
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    draw_number = db.Column(db.String(20), nullable=False)
    draw_date = db.Column(db.DateTime, nullable=False)
    numbers = db.Column(db.Text, nullable=False)  # JSON array as string
    bonus_numbers = db.Column(db.Text)  # JSON array as string
    divisions = db.Column(db.Text)  # JSON object as string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TicketScan(db.Model):
    __tablename__ = 'ticket_scan'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    lottery_type = db.Column(db.String(50))
    extracted_numbers = db.Column(db.Text)  # JSON array as string
    scan_results = db.Column(db.Text)  # JSON object as string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Core Functions
def get_latest_results(limit=10):
    """Get latest lottery results with proper data handling"""
    try:
        results = db.session.execute(text("""
            SELECT lottery_type, draw_number, draw_date, numbers, bonus_numbers
            FROM lottery_result 
            ORDER BY draw_date DESC, id DESC 
            LIMIT :limit
        """), {'limit': limit}).fetchall()
        
        processed_results = []
        for result in results:
            try:
                # Parse numbers safely
                numbers = json.loads(result.numbers) if result.numbers else []
                bonus_numbers = json.loads(result.bonus_numbers) if result.bonus_numbers else []
                
                processed_results.append({
                    'lottery_type': result.lottery_type,
                    'draw_number': str(result.draw_number),
                    'draw_date': result.draw_date.strftime('%Y-%m-%d') if result.draw_date else '',
                    'numbers': numbers,
                    'bonus_numbers': bonus_numbers
                })
            except Exception as e:
                logger.error(f"Error processing result {result}: {e}")
                continue
                
        return processed_results
    except Exception as e:
        logger.error(f"Error fetching latest results: {e}")
        return []

def get_frequency_data():
    """Get number frequency data with proper error handling"""
    try:
        results = db.session.execute(text("""
            SELECT numbers FROM lottery_result 
            WHERE numbers IS NOT NULL AND numbers != ''
        """)).fetchall()
        
        frequency = {}
        for result in results:
            try:
                numbers = json.loads(result.numbers)
                for num in numbers:
                    if isinstance(num, int):
                        frequency[num] = frequency.get(num, 0) + 1
            except Exception as e:
                logger.error(f"Error parsing numbers {result.numbers}: {e}")
                continue
        
        # Get top 10 most frequent numbers
        top_numbers = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'labels': [str(num) for num, _ in top_numbers],
            'data': [freq for _, freq in top_numbers],
            'total_draws': len(results)
        }
    except Exception as e:
        logger.error(f"Error getting frequency data: {e}")
        return {'labels': [], 'data': [], 'total_draws': 0}

def process_ticket_with_ai(image_path):
    """Process lottery ticket using Anthropic Claude"""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY'))
        
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data.hex()
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract lottery numbers from this ticket image. Return only a JSON object with the lottery type and numbers array."
                    }
                ]
            }]
        )
        
        return message.content[0].text
    except Exception as e:
        logger.error(f"Error processing ticket with AI: {e}")
        return None

# Routes
@app.route('/')
def home():
    """Home page with lottery results and analytics"""
    latest_results = get_latest_results(10)
    frequency_data = get_frequency_data()
    
    return render_template('home.html', 
                         results=latest_results,
                         frequency_data=frequency_data)

@app.route('/api/frequency')
def api_frequency():
    """API endpoint for frequency data"""
    data = get_frequency_data()
    return jsonify(data)

@app.route('/scanner')
def scanner():
    """Ticket scanner page"""
    return render_template('scanner.html')

@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    """Process uploaded ticket image"""
    if 'ticket_image' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('scanner'))
    
    file = request.files['ticket_image']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('scanner'))
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)
        
        # Process with AI
        scan_result = process_ticket_with_ai(file_path)
        
        # Save scan record
        scan_record = TicketScan(
            filename=filename,
            scan_results=scan_result
        )
        db.session.add(scan_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': scan_result,
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Error scanning ticket: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/results')
def results():
    """All lottery results page"""
    all_results = get_latest_results(50)
    return render_template('results.html', results=all_results)

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)