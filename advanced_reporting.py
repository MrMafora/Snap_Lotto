"""
Advanced Reporting System
Phase 4 Implementation - Comprehensive Analytics and Export Features
"""

import io
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg
from flask import Blueprint, render_template, jsonify, send_file, request
from models import db, LotteryResult
from sqlalchemy import text
from predictive_analytics import get_lottery_predictions

logger = logging.getLogger(__name__)
reporting_bp = Blueprint('reporting', __name__, url_prefix='/reporting')

class ReportGenerator:
    """Advanced report generation system"""
    
    def __init__(self):
        self.report_cache = {}
        self.chart_styles = {
            'primary_color': '#2E86AB',
            'secondary_color': '#A23B72', 
            'accent_color': '#F18F01',
            'background_color': '#F8F9FA'
        }
    
    def generate_comprehensive_report(self, lottery_type=None, date_range=30):
        """Generate a comprehensive lottery analysis report"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=date_range)
            
            # Build query
            query_conditions = ["draw_date >= :start_date", "draw_date <= :end_date"]
            params = {'start_date': start_date, 'end_date': end_date}
            
            if lottery_type:
                query_conditions.append("lottery_type = :lottery_type")
                params['lottery_type'] = lottery_type
            
            query = text(f"""
                SELECT * FROM lottery_result 
                WHERE {' AND '.join(query_conditions)}
                ORDER BY draw_date DESC, lottery_type
            """)
            
            results = db.session.execute(query, params).fetchall()
            
            if not results:
                return {'error': 'No data found for the specified criteria'}
            
            # Generate report sections
            report = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'date_range': f"{start_date} to {end_date}",
                    'lottery_type': lottery_type or 'All Types',
                    'total_draws': len(results)
                },
                'summary_statistics': self._generate_summary_stats(results),
                'frequency_analysis': self._generate_frequency_analysis(results),
                'trend_analysis': self._generate_trend_analysis(results),
                'pattern_insights': self._generate_pattern_insights(results),
                'predictive_insights': self._generate_predictive_insights(lottery_type),
                'charts': self._generate_chart_data(results)
            }
            
            logger.info(f"Generated comprehensive report for {len(results)} draws")
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {'error': str(e)}
    
    def _generate_summary_stats(self, results):
        """Generate summary statistics"""
        lottery_types = defaultdict(int)
        draw_dates = []
        total_jackpots = defaultdict(list)
        
        for result in results:
            lottery_types[result.lottery_type] += 1
            draw_dates.append(result.draw_date)
            
            # Extract jackpot information if available
            if hasattr(result, 'divisions') and result.divisions:
                try:
                    divisions = json.loads(result.divisions) if isinstance(result.divisions, str) else result.divisions
                    if isinstance(divisions, list) and divisions:
                        # Look for Division 1 (jackpot)
                        for div in divisions:
                            if isinstance(div, dict) and div.get('division') in ['1', 'Division 1']:
                                amount = div.get('amount', 0)
                                if amount:
                                    total_jackpots[result.lottery_type].append(amount)
                except:
                    continue
        
        return {
            'total_draws': len(results),
            'lottery_types': dict(lottery_types),
            'date_range': {
                'earliest': min(draw_dates).isoformat() if draw_dates else None,
                'latest': max(draw_dates).isoformat() if draw_dates else None
            },
            'jackpot_totals': {
                lottery_type: {
                    'count': len(amounts),
                    'total': sum(amounts),
                    'average': sum(amounts) / len(amounts) if amounts else 0,
                    'highest': max(amounts) if amounts else 0
                }
                for lottery_type, amounts in total_jackpots.items()
            }
        }
    
    def _generate_frequency_analysis(self, results):
        """Generate detailed frequency analysis"""
        frequency_data = defaultdict(lambda: defaultdict(int))
        all_numbers = defaultdict(list)
        
        for result in results:
            lottery_type = result.lottery_type
            
            # Parse main numbers
            if result.main_numbers:
                try:
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                    for num in numbers:
                        frequency_data[lottery_type][num] += 1
                        all_numbers[lottery_type].append(num)
                except:
                    continue
            
            # Parse bonus numbers
            if result.bonus_numbers:
                try:
                    bonus = json.loads(result.bonus_numbers.replace("'", '"'))
                    if isinstance(bonus, list):
                        for num in bonus:
                            frequency_data[lottery_type][f"bonus_{num}"] += 1
                    elif isinstance(bonus, int):
                        frequency_data[lottery_type][f"bonus_{bonus}"] += 1
                except:
                    continue
        
        # Generate insights
        insights = {}
        for lottery_type, numbers in all_numbers.items():
            if numbers:
                freq_dict = frequency_data[lottery_type]
                main_numbers = [k for k in freq_dict.keys() if not str(k).startswith('bonus_')]
                
                if main_numbers:
                    frequencies = [freq_dict[num] for num in main_numbers]
                    insights[lottery_type] = {
                        'most_frequent': sorted([(num, freq_dict[num]) for num in main_numbers], 
                                              key=lambda x: x[1], reverse=True)[:10],
                        'least_frequent': sorted([(num, freq_dict[num]) for num in main_numbers], 
                                               key=lambda x: x[1])[:10],
                        'avg_frequency': sum(frequencies) / len(frequencies) if frequencies else 0,
                        'total_unique_numbers': len(main_numbers)
                    }
        
        return insights
    
    def _generate_trend_analysis(self, results):
        """Generate trend analysis over time"""
        trends = defaultdict(lambda: defaultdict(list))
        
        # Group by time periods
        for result in results:
            date = result.draw_date
            lottery_type = result.lottery_type
            
            # Monthly trends
            month_key = f"{date.year}-{date.month:02d}"
            trends[lottery_type]['monthly'][month_key] = trends[lottery_type]['monthly'].get(month_key, 0) + 1
            
            # Weekly trends  
            week_key = date.strftime("%Y-W%U")
            trends[lottery_type]['weekly'][week_key] = trends[lottery_type]['weekly'].get(week_key, 0) + 1
            
            # Extract jackpot trends if available
            if hasattr(result, 'divisions') and result.divisions:
                try:
                    divisions = json.loads(result.divisions) if isinstance(result.divisions, str) else result.divisions
                    if isinstance(divisions, list):
                        for div in divisions:
                            if isinstance(div, dict) and div.get('division') in ['1', 'Division 1']:
                                amount = div.get('amount', 0)
                                if amount:
                                    trends[lottery_type]['jackpot_trend'].append({
                                        'date': date.isoformat(),
                                        'amount': amount
                                    })
                except:
                    continue
        
        return dict(trends)
    
    def _generate_pattern_insights(self, results):
        """Generate pattern insights and anomalies"""
        patterns = {}
        
        for lottery_type in set(result.lottery_type for result in results):
            type_results = [r for r in results if r.lottery_type == lottery_type]
            
            # Analyze number patterns
            consecutive_counts = 0
            even_odd_patterns = {'even_dominant': 0, 'odd_dominant': 0, 'balanced': 0}
            sum_ranges = {'low': 0, 'medium': 0, 'high': 0}
            
            for result in type_results:
                if result.main_numbers:
                    try:
                        numbers = json.loads(result.main_numbers.replace("'", '"'))
                        if isinstance(numbers, list) and len(numbers) > 1:
                            # Check for consecutive numbers
                            sorted_nums = sorted(numbers)
                            for i in range(len(sorted_nums) - 1):
                                if sorted_nums[i+1] - sorted_nums[i] == 1:
                                    consecutive_counts += 1
                                    break
                            
                            # Even/odd analysis
                            evens = sum(1 for n in numbers if n % 2 == 0)
                            odds = len(numbers) - evens
                            
                            if evens > odds:
                                even_odd_patterns['even_dominant'] += 1
                            elif odds > evens:
                                even_odd_patterns['odd_dominant'] += 1
                            else:
                                even_odd_patterns['balanced'] += 1
                            
                            # Sum range analysis
                            total = sum(numbers)
                            if total < 100:
                                sum_ranges['low'] += 1
                            elif total < 200:
                                sum_ranges['medium'] += 1
                            else:
                                sum_ranges['high'] += 1
                    except:
                        continue
            
            patterns[lottery_type] = {
                'consecutive_frequency': consecutive_counts / len(type_results) if type_results else 0,
                'even_odd_distribution': even_odd_patterns,
                'sum_range_distribution': sum_ranges,
                'total_analyzed': len(type_results)
            }
        
        return patterns
    
    def _generate_predictive_insights(self, lottery_type):
        """Generate predictive insights using the prediction engine"""
        if lottery_type:
            return get_lottery_predictions(lottery_type, 365)
        else:
            # Get predictions for all lottery types
            predictions = {}
            lottery_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'PowerBall', 'POWERBALL PLUS', 'DAILY LOTTO']
            
            for ltype in lottery_types:
                pred = get_lottery_predictions(ltype, 365)
                if pred:
                    predictions[ltype] = pred
            
            return predictions
    
    def _generate_chart_data(self, results):
        """Generate data for charts and visualizations"""
        chart_data = {}
        
        # Frequency chart data
        frequency_data = defaultdict(lambda: defaultdict(int))
        for result in results:
            if result.main_numbers:
                try:
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                    for num in numbers:
                        frequency_data[result.lottery_type][num] += 1
                except:
                    continue
        
        chart_data['frequency'] = {}
        for lottery_type, freq_dict in frequency_data.items():
            sorted_freq = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:20]
            chart_data['frequency'][lottery_type] = {
                'numbers': [str(num) for num, _ in sorted_freq],
                'frequencies': [freq for _, freq in sorted_freq]
            }
        
        # Timeline chart data
        timeline_data = defaultdict(lambda: defaultdict(int))
        for result in results:
            date_key = result.draw_date.strftime('%Y-%m')
            timeline_data[result.lottery_type][date_key] += 1
        
        chart_data['timeline'] = {}
        for lottery_type, dates in timeline_data.items():
            sorted_dates = sorted(dates.items())
            chart_data['timeline'][lottery_type] = {
                'dates': [date for date, _ in sorted_dates],
                'counts': [count for _, count in sorted_dates]
            }
        
        return chart_data
    
    def export_to_excel(self, report_data):
        """Export report data to Excel format"""
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([report_data['summary_statistics']])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Frequency analysis
                if 'frequency_analysis' in report_data:
                    for lottery_type, freq_data in report_data['frequency_analysis'].items():
                        if 'most_frequent' in freq_data:
                            freq_df = pd.DataFrame(freq_data['most_frequent'], 
                                                 columns=['Number', 'Frequency'])
                            sheet_name = f"Frequency_{lottery_type.replace(' ', '_')}"[:31]
                            freq_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Trend data
                if 'trend_analysis' in report_data:
                    for lottery_type, trend_data in report_data['trend_analysis'].items():
                        if 'monthly' in trend_data:
                            trend_df = pd.DataFrame(list(trend_data['monthly'].items()),
                                                  columns=['Month', 'Count'])
                            sheet_name = f"Trends_{lottery_type.replace(' ', '_')}"[:31]
                            trend_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return None
    
    def generate_visualization(self, chart_type, data, lottery_type=None):
        """Generate matplotlib visualizations"""
        try:
            plt.style.use('seaborn-v0_8')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if chart_type == 'frequency':
                # Frequency bar chart
                if lottery_type and lottery_type in data:
                    chart_data = data[lottery_type]
                    ax.bar(chart_data['numbers'][:15], chart_data['frequencies'][:15],
                          color=self.chart_styles['primary_color'])
                    ax.set_title(f'Number Frequency - {lottery_type}', fontsize=16, fontweight='bold')
                    ax.set_xlabel('Numbers', fontsize=12)
                    ax.set_ylabel('Frequency', fontsize=12)
                    plt.xticks(rotation=45)
            
            elif chart_type == 'timeline':
                # Timeline chart
                if lottery_type and lottery_type in data:
                    chart_data = data[lottery_type]
                    ax.plot(chart_data['dates'], chart_data['counts'], 
                           marker='o', linewidth=2, color=self.chart_styles['secondary_color'])
                    ax.set_title(f'Draw Frequency Over Time - {lottery_type}', fontsize=16, fontweight='bold')
                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Number of Draws', fontsize=12)
                    plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return None

# Global report generator
report_generator = ReportGenerator()

@reporting_bp.route('/dashboard')
def reporting_dashboard():
    """Advanced reporting dashboard"""
    return render_template('reporting/dashboard.html')

@reporting_bp.route('/api/generate-report')
def api_generate_report():
    """API endpoint to generate reports"""
    lottery_type = request.args.get('lottery_type')
    date_range = int(request.args.get('date_range', 30))
    
    report = report_generator.generate_comprehensive_report(lottery_type, date_range)
    return jsonify(report)

@reporting_bp.route('/api/export-excel')
def api_export_excel():
    """Export report to Excel"""
    lottery_type = request.args.get('lottery_type')
    date_range = int(request.args.get('date_range', 30))
    
    report = report_generator.generate_comprehensive_report(lottery_type, date_range)
    
    if 'error' in report:
        return jsonify(report), 400
    
    excel_file = report_generator.export_to_excel(report)
    
    if excel_file:
        filename = f"lottery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(excel_file, 
                        as_attachment=True, 
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        return jsonify({'error': 'Failed to generate Excel export'}), 500

@reporting_bp.route('/api/chart/<chart_type>')
def api_generate_chart(chart_type):
    """Generate chart visualization"""
    lottery_type = request.args.get('lottery_type')
    date_range = int(request.args.get('date_range', 30))
    
    # Get chart data
    report = report_generator.generate_comprehensive_report(lottery_type, date_range)
    
    if 'error' in report or 'charts' not in report:
        return jsonify({'error': 'Unable to generate chart data'}), 400
    
    # Generate visualization
    chart_data = report['charts'].get(chart_type, {})
    img_buffer = report_generator.generate_visualization(chart_type, chart_data, lottery_type)
    
    if img_buffer:
        return send_file(img_buffer, mimetype='image/png')
    else:
        return jsonify({'error': 'Failed to generate chart'}), 500