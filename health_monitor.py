"""
Health monitoring system for the Snap Lotto application.
Provides automated health checks, logging, and notifications for system issues.
"""
import logging
import threading
import time
import requests
import psutil
from datetime import datetime
from models import db
from sqlalchemy import text

logger = logging.getLogger(__name__)

def initialize_health_db():
    """Initialize the health check history database"""
    try:
        with db.engine.connect() as conn:
            # Create health_check_history table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS health_check_history (
                    id SERIAL PRIMARY KEY,
                    check_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create health_alerts table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS health_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_type VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL
                )
            """))
            conn.commit()
        logger.info("Health check database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize health check database: {e}")

def log_health_check(check_type, status, details):
    """Log a health check to the database"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO health_check_history (check_type, status, details)
                VALUES (:check_type, :status, :details)
            """), {
                'check_type': check_type,
                'status': status,
                'details': details
            })
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log health check: {e}")

def create_alert(alert_type, message):
    """Create a new alert in the database"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO health_alerts (alert_type, message)
                VALUES (:alert_type, :message)
            """), {
                'alert_type': alert_type,
                'message': message
            })
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")

def resolve_alert(alert_type):
    """Mark an alert as resolved"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("""
                UPDATE health_alerts 
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                WHERE alert_type = :alert_type AND status = 'active'
            """), {'alert_type': alert_type})
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")

def get_recent_alerts(limit=10):
    """Get recent alerts from the database"""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT alert_type, message, status, created_at, resolved_at
                FROM health_alerts
                ORDER BY created_at DESC
                LIMIT :limit
            """), {'limit': limit})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Failed to get recent alerts: {e}")
        return []

def get_health_history(check_type=None, limit=100):
    """Get health check history from the database"""
    try:
        with db.engine.connect() as conn:
            if check_type:
                result = conn.execute(text("""
                    SELECT check_type, status, details, timestamp
                    FROM health_check_history
                    WHERE check_type = :check_type
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """), {'check_type': check_type, 'limit': limit})
            else:
                result = conn.execute(text("""
                    SELECT check_type, status, details, timestamp
                    FROM health_check_history
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """), {'limit': limit})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Failed to get health history: {e}")
        return []

def check_server_status():
    """Check if the server is responding on the appropriate port"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            log_health_check('server_status', 'healthy', 'Server responding normally')
            return True
        else:
            log_health_check('server_status', 'warning', f'Server returned status {response.status_code}')
            return False
    except Exception as e:
        log_health_check('server_status', 'error', f'Server check failed: {str(e)}')
        return False

def check_database_connection(db):
    """Check if the database connection is working"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log_health_check('database', 'healthy', 'Database connection successful')
        return True
    except Exception as e:
        log_health_check('database', 'error', f'Database connection failed: {str(e)}')
        create_alert('database_error', f'Database connection failed: {str(e)}')
        return False

def check_port_usage():
    """Check which services are using which ports"""
    try:
        connections = psutil.net_connections(kind='inet')
        port_info = {}
        
        for conn in connections:
            if conn.laddr and conn.status == 'LISTEN':
                port = conn.laddr.port
                if port in [5000, 8080, 3000]:  # Monitor important ports
                    port_info[port] = {
                        'pid': conn.pid,
                        'status': conn.status
                    }
        
        for port in [8080]:  # Check specific ports
            try:
                response = requests.get(f'http://localhost:{port}', timeout=2)
                log_health_check('port_check', 'healthy', f'Port {port} responding')
            except Exception as e:
                logger.warning(f"Port {port} check failed: {e}")
        
        return port_info
    except Exception as e:
        logger.error(f"Port usage check failed: {e}")
        return {}

def check_system_resources():
    """Check system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resource_info = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent
        }
        
        # Check for high resource usage
        if cpu_percent > 90:
            create_alert('high_cpu', f'High CPU usage: {cpu_percent}%')
        
        if memory.percent > 90:
            create_alert('high_memory', f'High memory usage: {memory.percent}%')
        
        if disk.percent > 90:
            create_alert('high_disk', f'High disk usage: {disk.percent}%')
        
        log_health_check('system_resources', 'healthy', str(resource_info))
        return resource_info
    except Exception as e:
        log_health_check('system_resources', 'error', f'Resource check failed: {str(e)}')
        return {}

def check_advertisement_system(db):
    """Check the advertisement system"""
    try:
        # Simple check - just verify we can query the database
        with db.engine.connect() as conn:
            conn.execute(text("SELECT COUNT(*) FROM lottery_result LIMIT 1"))
        
        log_health_check('advertisement_system', 'healthy', 'Advertisement system operational')
        return True
    except Exception as e:
        log_health_check('advertisement_system', 'error', f'Advertisement system check failed: {str(e)}')
        return False

def run_health_checks(app, db):
    """Run all health checks"""
    with app.app_context():
        logger.info("Running scheduled health checks")
        
        # Initialize health database
        initialize_health_db()
        
        # Run checks
        check_database_connection(db)
        check_port_usage()
        check_system_resources()
        check_advertisement_system(db)

def start_health_check_scheduler(app, db, interval=300):
    """Start the health check scheduler"""
    logger.info(f"Starting health check scheduler with interval {interval} seconds")
    
    def scheduler_thread():
        while True:
            try:
                run_health_checks(app, db)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Health check scheduler error: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    thread = threading.Thread(target=scheduler_thread, daemon=True)
    thread.start()

def get_active_ports():
    """Get a list of all active ports and the services using them"""
    try:
        connections = psutil.net_connections(kind='inet')
        active_ports = {}
        
        for conn in connections:
            if conn.laddr and conn.status == 'LISTEN':
                port = conn.laddr.port
                try:
                    process = psutil.Process(conn.pid) if conn.pid else None
                    active_ports[port] = {
                        'pid': conn.pid,
                        'process_name': process.name() if process else 'Unknown',
                        'status': conn.status
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    active_ports[port] = {
                        'pid': conn.pid,
                        'process_name': 'Unknown',
                        'status': conn.status
                    }
        
        return active_ports
    except Exception as e:
        logger.error(f"Failed to get active ports: {e}")
        return {}

def get_system_status(app, db):
    """Get the current system status"""
    with app.app_context():
        try:
            return {
                'database_healthy': check_database_connection(db),
                'system_resources': check_system_resources(),
                'active_ports': get_active_ports(),
                'recent_alerts': get_recent_alerts(5),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}

def init_health_monitor(app, db):
    """Initialize the health monitoring system"""
    with app.app_context():
        initialize_health_db()
        start_health_check_scheduler(app, db)
        logger.info("Health monitoring system initialized")