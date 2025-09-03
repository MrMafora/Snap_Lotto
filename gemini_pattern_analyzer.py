"""
AI-Powered Lottery Pattern Analyzer using Google Gemini
Advanced pattern detection and analysis for South African lottery data
"""

import json
import logging
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import psycopg2
from datetime import datetime, timedelta
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY"))

class PatternAnalysis(BaseModel):
    """Pattern analysis result structure"""
    pattern_type: str
    confidence: float
    description: str
    evidence: List[str]
    recommendation: str

class GameTypeAnalysis(BaseModel):
    """Game type analysis result structure"""  
    game_type: str
    total_draws: int
    unique_patterns: int
    hot_sequences: List[List[int]]
    cold_sequences: List[List[int]]
    ai_insights: str

def get_lottery_data_for_ai(lottery_type: str = None, days: int = 180) -> Dict[str, Any]:
    """Fetch lottery data for AI analysis"""
    try:
        connection_string = os.environ.get('DATABASE_URL')
        data_by_type = {}
        
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Get recent draws with date filtering
                cutoff_date = (datetime.now() - timedelta(days=days)).date()
                
                if lottery_type and lottery_type != 'all':
                    query = """
                        SELECT lottery_type, main_numbers, bonus_numbers, draw_date, draw_number
                        FROM lottery_results 
                        WHERE draw_date >= %s AND lottery_type = %s AND main_numbers IS NOT NULL
                        ORDER BY draw_date DESC, lottery_type
                    """
                    cur.execute(query, (cutoff_date, lottery_type))
                else:
                    query = """
                        SELECT lottery_type, main_numbers, bonus_numbers, draw_date, draw_number
                        FROM lottery_results 
                        WHERE draw_date >= %s AND main_numbers IS NOT NULL
                        ORDER BY draw_date DESC, lottery_type
                    """
                    cur.execute(query, (cutoff_date,))
                
                results = cur.fetchall()
                
                for row in results:
                    game_type, main_numbers, bonus_numbers, draw_date, draw_number = row
                    
                    if game_type not in data_by_type:
                        data_by_type[game_type] = {
                            'draws': [],
                            'all_numbers': [],
                            'draw_dates': [],
                            'draw_numbers': []
                        }
                    
                    # Parse main numbers
                    parsed_main = []
                    if main_numbers:
                        if isinstance(main_numbers, str):
                            if main_numbers.startswith('{') and main_numbers.endswith('}'):
                                numbers_str = main_numbers.strip('{}')
                                if numbers_str:
                                    parsed_main = [int(x.strip()) for x in numbers_str.split(',')]
                            else:
                                try:
                                    parsed_main = json.loads(main_numbers)
                                except:
                                    pass
                        elif isinstance(main_numbers, list):
                            parsed_main = main_numbers
                    
                    # Parse bonus numbers
                    parsed_bonus = []
                    if bonus_numbers:
                        if isinstance(bonus_numbers, str):
                            if bonus_numbers.startswith('{') and bonus_numbers.endswith('}'):
                                numbers_str = bonus_numbers.strip('{}')
                                if numbers_str:
                                    parsed_bonus = [int(x.strip()) for x in numbers_str.split(',')]
                            else:
                                try:
                                    parsed_bonus = json.loads(bonus_numbers)
                                except:
                                    pass
                        elif isinstance(bonus_numbers, list):
                            parsed_bonus = bonus_numbers
                    
                    draw_info = {
                        'main_numbers': sorted(parsed_main) if parsed_main else [],
                        'bonus_numbers': sorted(parsed_bonus) if parsed_bonus else [],
                        'draw_date': draw_date.isoformat() if draw_date else None,
                        'draw_number': draw_number
                    }
                    
                    data_by_type[game_type]['draws'].append(draw_info)
                    data_by_type[game_type]['all_numbers'].extend(parsed_main)
                    data_by_type[game_type]['draw_dates'].append(draw_date.isoformat() if draw_date else None)
                    data_by_type[game_type]['draw_numbers'].append(draw_number)
        
        return data_by_type
        
    except Exception as e:
        logger.error(f"Error fetching lottery data: {e}")
        return {}

def analyze_number_patterns_with_ai(lottery_data: Dict[str, Any]) -> List[PatternAnalysis]:
    """Use Gemini AI to analyze lottery number patterns"""
    try:
        # Prepare data summary for AI
        analysis_prompt = """
        Analyze the following South African lottery data and identify meaningful patterns in winning numbers.
        Focus on mathematical patterns, sequences, trends, and statistical anomalies.
        
        Data Summary:
        """
        
        for game_type, data in lottery_data.items():
            analysis_prompt += f"\n{game_type}:\n"
            analysis_prompt += f"- Total draws: {len(data['draws'])}\n"
            analysis_prompt += f"- Recent 10 draws: {data['draws'][:10]}\n"
            analysis_prompt += f"- Number frequency: {dict(Counter(data['all_numbers']).most_common(10))}\n"
        
        analysis_prompt += """
        
        Please identify:
        1. Sequential number patterns (consecutive numbers, arithmetic sequences)
        2. Statistical anomalies (unusually hot/cold numbers)
        3. Date-based patterns (patterns related to draw dates)
        4. Cross-game correlations (patterns across different lottery types)
        5. Mathematical relationships (sum patterns, odd/even distributions)
        
        For each pattern found, provide:
        - Pattern type
        - Confidence level (0.0-1.0)
        - Clear description
        - Supporting evidence
        - Actionable recommendation
        
        Format as JSON array of pattern objects.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=List[PatternAnalysis],
                temperature=0.3
            )
        )
        
        if response.text:
            patterns = json.loads(response.text)
            return [PatternAnalysis(**p) for p in patterns]
        
        return []
        
    except Exception as e:
        logger.error(f"AI pattern analysis error: {e}")
        return []

def analyze_game_types_with_ai(lottery_data: Dict[str, Any]) -> List[GameTypeAnalysis]:
    """Use Gemini AI to analyze patterns specific to each game type"""
    try:
        game_analyses = []
        
        for game_type, data in lottery_data.items():
            if len(data['draws']) < 5:  # Skip if insufficient data
                continue
                
            game_prompt = f"""
            Analyze the {game_type} lottery game data for unique patterns and characteristics.
            
            Game Data:
            - Total draws: {len(data['draws'])}
            - Recent draws: {data['draws'][:20]}
            - All numbers frequency: {dict(Counter(data['all_numbers']).most_common(15))}
            - Draw numbers: {data['draw_numbers'][:10]}
            
            Please analyze:
            1. Hot number sequences (commonly drawn together)
            2. Cold number sequences (rarely drawn together)
            3. Game-specific patterns unique to {game_type}
            4. Statistical insights about this specific game
            5. Predictive insights based on historical trends
            
            Provide actionable insights for players of {game_type}.
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=game_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GameTypeAnalysis,
                    temperature=0.4
                )
            )
            
            if response.text:
                analysis_data = json.loads(response.text)
                analysis_data['game_type'] = game_type
                analysis_data['total_draws'] = len(data['draws'])
                game_analyses.append(GameTypeAnalysis(**analysis_data))
        
        return game_analyses
        
    except Exception as e:
        logger.error(f"Game type analysis error: {e}")
        return []

def generate_ai_insights_summary(pattern_analyses: List[PatternAnalysis], 
                                game_analyses: List[GameTypeAnalysis]) -> str:
    """Generate a comprehensive AI insights summary"""
    try:
        summary_prompt = f"""
        Based on the following lottery pattern analyses, provide a comprehensive summary 
        of key insights for South African lottery players.
        
        Pattern Analyses: {[p.dict() for p in pattern_analyses]}
        Game Type Analyses: {[g.dict() for g in game_analyses]}
        
        Create a concise, actionable summary highlighting:
        1. Most significant patterns discovered
        2. Game-specific recommendations
        3. Statistical insights
        4. Strategic advice for players
        
        Keep it professional, factual, and focused on data-driven insights.
        Limit to 200-300 words.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=summary_prompt,
            config=types.GenerateContentConfig(
                temperature=0.5
            )
        )
        
        return response.text if response.text else "No insights generated."
        
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return "Unable to generate insights summary."

def get_comprehensive_ai_analysis(lottery_type: str = None, days: int = 180) -> Dict[str, Any]:
    """Get comprehensive AI analysis of lottery patterns"""
    try:
        # Map frontend lottery type to database value
        type_mapping = {
            'Lottery': 'LOTTO',
            'Lottery Plus 1': 'LOTTO PLUS 1', 
            'Lottery Plus 2': 'LOTTO PLUS 2',
            'Powerball': 'POWERBALL',
            'Powerball Plus': 'POWERBALL PLUS',
            'Daily Lottery': 'DAILY LOTTO'
        }
        
        if lottery_type and lottery_type != 'all':
            lottery_type = type_mapping.get(lottery_type, lottery_type)
        
        # Get lottery data
        lottery_data = get_lottery_data_for_ai(lottery_type, days)
        
        if not lottery_data:
            return {
                'error': 'No lottery data available for analysis',
                'pattern_analyses': [],
                'game_analyses': [],
                'ai_summary': 'Insufficient data for AI analysis.'
            }
        
        # Perform AI analyses
        pattern_analyses = analyze_number_patterns_with_ai(lottery_data)
        game_analyses = analyze_game_types_with_ai(lottery_data)
        ai_summary = generate_ai_insights_summary(pattern_analyses, game_analyses)
        
        return {
            'success': True,
            'data_period_days': days,
            'lottery_type': lottery_type or 'all',
            'games_analyzed': list(lottery_data.keys()),
            'total_draws_analyzed': sum(len(data['draws']) for data in lottery_data.values()),
            'pattern_analyses': [p.dict() for p in pattern_analyses],
            'game_analyses': [g.dict() for g in game_analyses],
            'ai_summary': ai_summary,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive AI analysis error: {e}")
        return {
            'error': str(e),
            'pattern_analyses': [],
            'game_analyses': [],
            'ai_summary': 'Analysis failed due to technical error.'
        }