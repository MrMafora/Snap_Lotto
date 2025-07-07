"""
Performance Monitoring Dashboard
Phase 3 Implementation - Real-time System Monitoring
"""

import psutil
import time
import json
import logging
from datetime import datetime, timedelta
from collections import deque
from flask import Blueprint, render_template, jsonify
from models import db, LotteryResult
from database_utils import get_database_stats
from sqlalchemy import text

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')
logger = logging.getLogger(__name__)

class SystemMonitor:
    """Real-time system monitoring class"""
    
    def __init__(self, max_data_points=100):
        self.max_data_points = max_data_points
        self.cpu_data = deque(maxlen=max_data_points)
        self.memory_data = deque(maxlen=max_data_points)
        self.disk_data = deque(maxlen=max_data_points)
        self.response_times = deque(maxlen=max_data_points)
        self.error_count = 0
        self.start_time = datetime.now()
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        timestamp = datetime.now().isoformat()
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_data.append({'timestamp': timestamp, 'value': cpu_percent})
        
        # Memory Usage
        memory = psutil.virtual_memory()
        self.memory_data.append({
            'timestamp': timestamp, 
            'value': memory.percent,
            'used_gb': round(memory.used / (1024**3), 2),
            'total_gb': round(memory.total / (1024**3), 2)
        })
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.disk_data.append({
            'timestamp': timestamp,
            'value': disk_percent,
            'used_gb': round(disk.used / (1024**3), 2),
            'total_gb': round(disk.total / (1024**3), 2)
        })
        
        return {
            'cpu': cpu_percent,
            'memory': memory.percent,
            'disk': disk_percent,
            'timestamp': timestamp
        }
    
    def get_current_metrics(self):
        """Get current system metrics"""
        return {
            'cpu_data': list(self.cpu_data),
            'memory_data': list(self.memory_data),
            'disk_data': list(self.disk_data),
            'response_times': list(self.response_times),
            'error_count': self.error_count,
            'uptime': str(datetime.now() - self.start_time)
        }
    
    def add_response_time(self, response_time_ms):
        """Add response time measurement"""
        self.response_times.append({
            'timestamp': datetime.now().isoformat(),
            'value': response_time_ms
        })
    
    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1

# Global monitor instance
system_monitor = SystemMonitor()

class DatabaseMonitor:
    """Database performance monitoring"""
    
    @staticmethod
    def get_database_performance():
        """Get database performance metrics"""
        try:
            # Connection count
            conn_query = text("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            
            # Table sizes
            size_query = text("""
                SELECT 
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) as size,
                    pg_total_relation_size(relid) as size_bytes
                FROM pg_stat_user_tables 
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 10
            """)
            
            # Query performance
            query_stats = text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE query NOT LIKE '%pg_stat%'
                ORDER BY mean_time DESC 
                LIMIT 5
            """)
            
            connections = db.session.execute(conn_query).scalar()
            table_sizes = db.session.execute(size_query).fetchall()
            
            # Query stats might not be available if pg_stat_statements isn't enabled
            try:
                query_performance = db.session.execute(query_stats).fetchall()
            except:
                query_performance = []
            
            return {
                'active_connections': connections,
                'table_sizes': [dict(row._mapping) for row in table_sizes],
                'query_performance': [dict(row._mapping) for row in query_performance],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting database performance: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_lottery_data_stats():
        """Get lottery data specific statistics"""
        try:
            stats_query = text("""
                SELECT 
                    lottery_type,
                    COUNT(*) as total_records,
                    MAX(draw_date) as latest_draw,
                    MIN(draw_date) as earliest_draw,
                    MAX(draw_number) as highest_draw_number
                FROM lottery_results 
                GROUP BY lottery_type
                ORDER BY lottery_type
            """)
            
            result = db.session.execute(stats_query)
            return [dict(row._mapping) for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting lottery stats: {e}")
            return []

class AlertManager:
    """System alert management"""
    
    def __init__(self):
        self.alerts = deque(maxlen=50)
        self.alert_thresholds = {
            'cpu_high': 85,
            'memory_high': 90,
            'disk_high': 90,
            'response_time_high': 2000,  # ms
            'error_rate_high': 10  # errors per minute
        }
    
    def check_alerts(self, metrics):
        """Check for alert conditions"""
        alerts_triggered = []
        
        # CPU alert
        if metrics.get('cpu', 0) > self.alert_thresholds['cpu_high']:
            alert = {
                'type': 'cpu_high',
                'message': f"High CPU usage: {metrics['cpu']:.1f}%",
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            }
            alerts_triggered.append(alert)
            self.alerts.append(alert)
        
        # Memory alert
        if metrics.get('memory', 0) > self.alert_thresholds['memory_high']:
            alert = {
                'type': 'memory_high',
                'message': f"High memory usage: {metrics['memory']:.1f}%",
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            }
            alerts_triggered.append(alert)
            self.alerts.append(alert)
        
        # Disk alert
        if metrics.get('disk', 0) > self.alert_thresholds['disk_high']:
            alert = {
                'type': 'disk_high',
                'message': f"High disk usage: {metrics['disk']:.1f}%",
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            }
            alerts_triggered.append(alert)
            self.alerts.append(alert)
        
        return alerts_triggered
    
    def get_recent_alerts(self, limit=10):
        """Get recent alerts"""
        return list(self.alerts)[-limit:]

# Global alert manager
alert_manager = AlertManager()

@monitoring_bp.route('/dashboard')
def monitoring_dashboard():
    """Main monitoring dashboard"""
    return render_template('monitoring/dashboard.html')

@monitoring_bp.route('/api/system-metrics')
def api_system_metrics():
    """API endpoint for real-time system metrics"""
    try:
        # Collect fresh metrics
        current_metrics = system_monitor.collect_system_metrics()
        
        # Check for alerts
        alerts = alert_manager.check_alerts(current_metrics)
        
        # Get all monitoring data
        response_data = {
            'current': current_metrics,
            'historical': system_monitor.get_current_metrics(),
            'alerts': alerts,
            'recent_alerts': alert_manager.get_recent_alerts()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/database-metrics')
def api_database_metrics():
    """API endpoint for database performance metrics"""
    try:
        db_performance = DatabaseMonitor.get_database_performance()
        lottery_stats = DatabaseMonitor.get_lottery_data_stats()
        
        return jsonify({
            'performance': db_performance,
            'lottery_data': lottery_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/application-health')
def api_application_health():
    """Comprehensive application health check"""
    health_data = {
        'status': 'healthy',
        'checks': {},
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Database connectivity
        LotteryResult.query.first()
        health_data['checks']['database'] = 'healthy'
    except:
        health_data['checks']['database'] = 'unhealthy'
        health_data['status'] = 'unhealthy'
    
    try:
        # System resources
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        
        if cpu > 90 or memory > 95:
            health_data['checks']['resources'] = 'degraded'
            health_data['status'] = 'degraded'
        else:
            health_data['checks']['resources'] = 'healthy'
            
    except:
        health_data['checks']['resources'] = 'unknown'
    
    # Application-specific checks
    try:
        # Check if we have recent lottery data
        recent_data = LotteryResult.query.filter(
            LotteryResult.draw_date >= datetime.now().date() - timedelta(days=30)
        ).count()
        
        if recent_data > 0:
            health_data['checks']['data_freshness'] = 'healthy'
        else:
            health_data['checks']['data_freshness'] = 'warning'
            
    except:
        health_data['checks']['data_freshness'] = 'unknown'
    
    return jsonify(health_data)

def init_monitoring(app):
    """Initialize monitoring system"""
    app.register_blueprint(monitoring_bp)
    
    # Start background monitoring
    import threading
    
    def background_monitoring():
        """Background thread for continuous monitoring"""
        while True:
            try:
                system_monitor.collect_system_metrics()
                time.sleep(30)  # Collect metrics every 30 seconds
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    monitor_thread = threading.Thread(target=background_monitoring, daemon=True)
    monitor_thread.start()
    
    logger.info("Monitoring system initialized")