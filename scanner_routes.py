"""
Scanner Routes Module for Lottery Ticket Processing
Provides web interface for uploading and processing lottery tickets with Google Gemini 2.5 Pro
"""

import os
import json
import base64
import logging
import time
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai
import PIL.Image
import io
import re

logger = logging.getLogger(__name__)

def perform_ticket_match_analysis(ticket_data):
    """Compare ticket numbers against latest lottery results"""
    try:
        from models import db, LotteryResult
        
        lottery_type = ticket_data.get('lottery_type', '').upper()
        ticket_lines = ticket_data.get('all_lines', [])
        powerball_numbers = ticket_data.get('all_powerball', [])
        
        # Get latest lottery results for comparison
        latest_results = {}
        
        # Map ticket lottery types to database lottery types
        type_mapping = {
            'POWERBALL': ['POWERBALL', 'POWERBALL PLUS'],
            'LOTTO': ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2'],
            'DAILY LOTTO': ['DAILY LOTTO']
        }
        
        # Get relevant lottery types for this ticket
        relevant_types = type_mapping.get(lottery_type, [lottery_type])
        
        for lt in relevant_types:
            result = LotteryResult.query.filter_by(lottery_type=lt).order_by(LotteryResult.draw_date.desc()).first()
            if result:
                latest_results[lt] = result
        
        # Perform match analysis
        match_analysis = {
            'has_matches': False,
            'total_matches': 0,
            'enhanced_comparison': True,
            'message': f'Compared against latest draws for {lottery_type}',
            'comparison_timestamp': datetime.now().isoformat()
        }
        
        # Analyze each ticket line
        line_results = []
        for i, line in enumerate(ticket_lines):
            line_matches = analyze_ticket_line(line, powerball_numbers, i, latest_results, lottery_type)
            line_results.append(line_matches)
            
            if line_matches.get('has_matches', False):
                match_analysis['has_matches'] = True
                match_analysis['total_matches'] += line_matches.get('total_matches', 0)
        
        match_analysis['line_results'] = line_results
        
        # Add specific game comparisons for frontend
        if 'LOTTO' in latest_results:
            match_analysis['main_game'] = create_game_comparison(ticket_lines[0] if ticket_lines else [], [], latest_results['LOTTO'], 'LOTTO')
        
        if 'LOTTO PLUS 1' in latest_results:
            match_analysis['plus_1_game'] = create_game_comparison(ticket_lines[0] if ticket_lines else [], [], latest_results['LOTTO PLUS 1'], 'LOTTO PLUS 1')
        
        if 'LOTTO PLUS 2' in latest_results:
            match_analysis['plus_2_game'] = create_game_comparison(ticket_lines[0] if ticket_lines else [], [], latest_results['LOTTO PLUS 2'], 'LOTTO PLUS 2')
        
        if 'POWERBALL' in latest_results:
            match_analysis['main_game_results'] = create_game_comparison(ticket_lines[0] if ticket_lines else [], powerball_numbers, latest_results['POWERBALL'], 'POWERBALL')
        
        if 'POWERBALL PLUS' in latest_results:
            match_analysis['powerball_plus_results'] = create_game_comparison(ticket_lines[0] if ticket_lines else [], powerball_numbers, latest_results['POWERBALL PLUS'], 'POWERBALL PLUS')
        
        return match_analysis
        
    except Exception as e:
        logger.error(f"Error in match analysis: {e}")
        return {
            'has_matches': False,
            'total_matches': 0,
            'error': str(e),
            'message': 'Error comparing ticket numbers'
        }

def analyze_ticket_line(ticket_numbers, powerball_numbers, line_index, latest_results, lottery_type):
    """Analyze a single ticket line against lottery results"""
    line_result = {
        'line_index': line_index,
        'ticket_numbers': ticket_numbers,
        'has_matches': False,
        'total_matches': 0,
        'games_checked': []
    }
    
    for game_type, result in latest_results.items():
        winning_numbers = result.get_numbers_list()
        bonus_numbers = result.get_bonus_numbers_list()
        
        main_matches = len(set(ticket_numbers) & set(winning_numbers))
        bonus_match = False
        
        # Check bonus ball matches for LOTTO games
        if game_type.startswith('LOTTO') and bonus_numbers:
            bonus_match = bool(set(ticket_numbers) & set(bonus_numbers))
        
        # Check PowerBall matches
        powerball_match = False
        if game_type.startswith('POWERBALL') and powerball_numbers and bonus_numbers:
            powerball_match = bool(set(powerball_numbers) & set(bonus_numbers))
        
        game_matches = main_matches + (1 if bonus_match or powerball_match else 0)
        
        if game_matches > 0:
            line_result['has_matches'] = True
            line_result['total_matches'] += game_matches
        
        line_result['games_checked'].append({
            'game_type': game_type,
            'main_matches': main_matches,
            'bonus_match': bonus_match,
            'powerball_match': powerball_match,
            'total_matches': game_matches
        })
    
    return line_result

def create_game_comparison(ticket_numbers, powerball_numbers, lottery_result, game_type):
    """Create detailed game comparison for frontend display"""
    winning_numbers = lottery_result.get_numbers_list()
    bonus_numbers = lottery_result.get_bonus_numbers_list()
    
    main_matches = len(set(ticket_numbers) & set(winning_numbers))
    bonus_match = False
    powerball_match = False
    
    if game_type.startswith('LOTTO') and bonus_numbers:
        bonus_match = bool(set(ticket_numbers) & set(bonus_numbers))
    elif game_type.startswith('POWERBALL') and powerball_numbers and bonus_numbers:
        powerball_match = bool(set(powerball_numbers) & set(bonus_numbers))
    
    total_matches = main_matches + (1 if bonus_match or powerball_match else 0)
    
    return {
        'lottery_type': game_type,
        'main_matches': main_matches,
        'bonus_match': bonus_match,
        'powerball_match': powerball_match,
        'total_matches': total_matches,
        'winning_numbers': winning_numbers,
        'bonus_numbers': bonus_numbers,
        'draw_number': lottery_result.draw_number,
        'draw_date': lottery_result.get_formatted_date()
    }

def register_scanner_routes(app):
    """Register scanner routes with the Flask app"""
    
    @app.route('/ticket-scanner')
    def ticket_scanner():
        """Ticket scanner page for uploading lottery tickets"""
        return render_template('scanner/ticket_scanner.html')
    
    @app.route('/admin/scan-ticket')
    def admin_scan_ticket():
        """Admin ticket scanner page"""
        return render_template('admin/scan_ticket.html')
    
    @app.route('/api/scan-ticket', methods=['POST'])
    def api_scan_ticket():
        """API endpoint for processing uploaded ticket images with database storage"""
        start_time = time.time()
        file_path = None
        
        try:
            from models import db, ScannedTicket, LotteryResult
            
            if 'ticket_image' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['ticket_image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"ticket_{timestamp}_{filename}"
            file_path = os.path.join('uploads', safe_filename)
            
            # Ensure uploads directory exists
            os.makedirs('uploads', exist_ok=True)
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # Process with Google Gemini 2.5 Pro
            genai.configure(api_key=os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY'))
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Load image
            image = PIL.Image.open(file_path)
            
            prompt = """Extract lottery ticket data from this South African lottery ticket. 

CRITICAL INSTRUCTIONS:
1. Find ALL number rows - each row has main numbers
2. Find any bonus/powerball numbers for each row
3. Identify the lottery type (PowerBall, Lotto, Daily Lotto, etc.)
4. Extract draw date and draw number if visible
5. Return exactly this JSON format:

{
    "lottery_type": "PowerBall",
    "all_lines": [
        [9, 15, 37, 39, 50],
        [12, 26, 31, 32, 47]
    ],
    "all_powerball": ["7", "12"],
    "powerball_plus_included": "YES",
    "draw_date": "21/03/25",
    "draw_number": "1599",
    "ticket_cost": "R30.00"
}

Extract ALL visible data accurately."""
            
            response = model.generate_content([image, prompt])
            response_text = response.text
            
            logger.info(f"Gemini response: {response_text}")
            
            # Extract and clean JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                # Fix leading zeros in JSON (05 -> "05")
                json_text = re.sub(r'(\[|\,)\s*0(\d)', r'\1"0\2"', json_text)
                ticket_data = json.loads(json_text)
                
                # Perform match analysis against database
                match_results = perform_ticket_match_analysis(ticket_data)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Save to database
                scanned_ticket = ScannedTicket(
                    lottery_type=ticket_data.get('lottery_type', 'Unknown'),
                    ticket_lines=json.dumps(ticket_data.get('all_lines', [])),
                    powerball_numbers=json.dumps(ticket_data.get('all_powerball', [])),
                    draw_date=ticket_data.get('draw_date'),
                    draw_number=ticket_data.get('draw_number'),
                    ticket_cost=ticket_data.get('ticket_cost'),
                    powerball_plus_included=ticket_data.get('powerball_plus_included'),
                    original_filename=filename,
                    file_size=file_size,
                    match_results=json.dumps(match_results),
                    has_matches=match_results.get('has_matches', False),
                    total_matches=match_results.get('total_matches', 0),
                    gemini_response=response_text,
                    processing_time=processing_time
                )
                
                db.session.add(scanned_ticket)
                db.session.commit()
                
                logger.info(f"Saved scanned ticket {scanned_ticket.id} to database")
                
                # Clean up the file
                os.remove(file_path)
                
                # Prepare enhanced response
                response_data = ticket_data.copy()
                response_data.update(match_results)
                response_data['scan_id'] = scanned_ticket.id
                response_data['processing_time'] = processing_time
                
                return jsonify({
                    'success': True,
                    'data': response_data,
                    'message': 'Ticket processed and saved successfully'
                })
            else:
                return jsonify({'error': 'Could not extract ticket data'}), 400
                
        except Exception as e:
            logger.error(f"Error processing ticket: {e}")
            # Clean up file if it exists
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': f'Processing error: {str(e)}'}), 500
    
    logger.info("Scanner routes registered successfully")