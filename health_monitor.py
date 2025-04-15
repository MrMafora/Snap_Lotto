"""
Health monitoring system for the Snap Lotto application.
Provides automated health checks, logging, and notifications for system issues.
"""

import os
import logging
import time
import json
import socket
import urllib.request
import datetime
import threading
import sqlite3
from sqlalchemy import text
import psutil

# Set up logging
logger = logging.getLogger('health_monitor')
logger.setLevel(logging.INFO)

# Create a file handler
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(logs_dir, 'health_monitor.log'))
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Health check history database
health_db_path = os.path.join(os.getcwd(), 'instance', 'health_checks.db')

def initialize_health_db():
    """Initialize the health check history database"""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(health_db_path), exist_ok=True)
        
        conn = sqlite3.connect(health_db_path)
        cursor = conn.cursor()
        
        # Create health check history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_type TEXT,
            status TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create alerts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT,
            message TEXT,
            resolved BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Health check database initialized")
    except Exception as e:
        logger.error(f"Error initializing health check database: {str(e)}")

def log_health_check(check_type, status, details):
    """Log a health check to the database"""
    try:
        conn = sqlite3.connect(health_db_path)
        cursor = conn.cursor()
        
        # Convert details to JSON string if it's a dict
        if isinstance(details, dict):
            details = json.dumps(details)
            
        cursor.execute(
            "INSERT INTO health_checks (check_type, status, details) VALUES (?, ?, ?)",
            (check_type, status, details)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging health check: {str(e)}")

def create_alert(alert_type, message):
    """Create a new alert in the database"""
    try:
        conn = sqlite3.connect(health_db_path)
        cursor = conn.cursor()
        
        # Check if there's already an unresolved alert of this type
        cursor.execute(
            "SELECT id FROM alerts WHERE alert_type = ? AND resolved = 0",
            (alert_type,)
        )
        existing_alert = cursor.fetchone()
        
        if not existing_alert:
            cursor.execute(
                "INSERT INTO alerts (alert_type, message) VALUES (?, ?)",
                (alert_type, message)
            )
            logger.warning(f"ALERT: {alert_type} - {message}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")

def resolve_alert(alert_type):
    """Mark an alert as resolved"""
    try:
        conn = sqlite3.connect(health_db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE alerts SET resolved = 1, resolved_at = CURRENT_TIMESTAMP WHERE alert_type = ? AND resolved = 0",
            (alert_type,)
        )
        
        if cursor.rowcount > 0:
            logger.info(f"Alert resolved: {alert_type}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")

def get_recent_alerts(limit=10):
    """Get recent alerts from the database"""
    try:
        conn = sqlite3.connect(health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return alerts
    except Exception as e:
        logger.error(f"Error getting recent alerts: {str(e)}")
        return []

def get_health_history(check_type=None, limit=100):
    """Get health check history from the database"""
    try:
        conn = sqlite3.connect(health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if check_type:
            cursor.execute(
                "SELECT * FROM health_checks WHERE check_type = ? ORDER BY timestamp DESC LIMIT ?",
                (check_type, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM health_checks ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    except Exception as e:
        logger.error(f"Error getting health history: {str(e)}")
        return []

# Health check functions
def check_server_status():
    """Check if the server is responding on the appropriate port"""
    # Check port 5000 for development and port 8080 for production
    import os
    
    # In development, we check port 5000; in production, we check port 8080
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    if environment.lower() == 'production':
        # Production environment - check port 8080
        port_to_check = 8080
    else:
        # Development environment - check port 5000
        port_to_check = 5000
    
    port_status = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', port_to_check))
            port_status = True
    except Exception as e:
        logger.warning(f"Port {port_to_check} check failed: {str(e)}")
    
    # Log the results
    status = "OK" if port_status else "CRITICAL"
    details = {
        f"port_{port_to_check}": port_status
    }
    
    log_health_check("server_status", status, details)
    
    # Create or resolve alerts as needed
    if not port_status:
        create_alert(f"port_{port_to_check}_down", f"Application port ({port_to_check}) is not responding")
    else:
        resolve_alert(f"port_{port_to_check}_down")
        
        # Always resolve the other port alert to prevent false alerts
        other_port = 8080 if port_to_check == 5000 else 5000
        resolve_alert(f"port_{other_port}_down")
    
    return status, details

def check_database_connection(db):
    """Check if the database connection is working"""
    db_status = False
    details = {}
    
    try:
        # Simple query to check connection
        result = db.session.execute(text("SELECT 1")).scalar()
        db_status = result == 1
        
        # Get more detailed stats if connection is working
        if db_status:
            # Count tables
            result = db.session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            tables_count = result.scalar() or 0
            
            # Count records
            tables_data = {}
            for table in ['lottery_result', 'advertisement', 'user']:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    tables_data[table] = result.scalar() or 0
                except:
                    tables_data[table] = -1
            
            details = {
                "tables_count": tables_count,
                "tables_data": tables_data
            }
    except Exception as e:
        logger.warning(f"Database connection check failed: {str(e)}")
        details = {"error": str(e)}
    
    # Log the results
    status = "OK" if db_status else "CRITICAL"
    log_health_check("database_connection", status, details)
    
    # Create or resolve alerts
    if not db_status:
        create_alert("database_down", "Database connection failed")
    else:
        resolve_alert("database_down")
    
    return status, details

def check_port_usage():
    """Check which services are using which ports"""
    port_details = {}
    service_usage = {}
    
    # Define common ports to monitor (can be expanded as needed)
    monitored_ports = [5000, 8080, 80, 443, 3000, 3306, 5432, 27017, 6379, 9090, 9000]
    
    try:
        # Get all network connections
        connections = psutil.net_connections()
        
        # Filter for listening TCP connections (servers)
        for conn in connections:
            port = None
            # Handle different psutil connection address formats
            if hasattr(conn.laddr, '_asdict') and hasattr(conn.laddr, 'port'):  # Named tuple format
                port = conn.laddr.port
            elif isinstance(conn.laddr, tuple) and len(conn.laddr) > 1:  # Tuple format
                port = conn.laddr[1]
            else:
                continue
                
            if conn.status == 'LISTEN' and port is not None:
                # Add port even if not in monitored_ports to ensure we catch all active server ports
                if port not in port_details:
                    port_details[port] = {
                        "pid": conn.pid,
                        "status": conn.status,
                        "is_monitored": port in monitored_ports
                    }
                    
                    # Get process information for this port
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            port_details[port].update({
                                "process_name": process.name(),
                                "process_cmdline": " ".join(process.cmdline()),
                                "process_create_time": datetime.datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                                "process_username": process.username(),
                                "process_memory_percent": round(process.memory_percent(), 2)
                            })
                            
                            # Organize by service/process name for easier viewing
                            proc_name = process.name()
                            if proc_name not in service_usage:
                                service_usage[proc_name] = []
                            service_usage[proc_name].append(port)
                        except psutil.NoSuchProcess:
                            port_details[port]["process_info"] = "Process no longer exists"
        
        # Add service usage summary to the port details
        details = {
            "port_details": port_details,
            "service_usage": service_usage,
            "monitored_ports": monitored_ports,
            "total_listening_ports": len(port_details)
        }
        
        # Log the results
        status = "OK"
        log_health_check("port_usage", status, details)
        
        return status, details
    except Exception as e:
        logger.warning(f"Port usage check failed: {str(e)}")
        details = {"error": str(e)}
        status = "WARNING"
        log_health_check("port_usage", status, details)
        return status, details

def check_system_resources():
    """Check system resource usage"""
    try:
        # Get system stats
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        cpu_usage = psutil.cpu_percent(interval=1)
        
        details = {
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "cpu_usage": cpu_usage,
            "memory_available_mb": round(memory.available / (1024 * 1024)),
            "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2)
        }
        
        # Determine status based on thresholds
        status = "OK"
        
        if memory_usage > 90 or disk_usage > 90 or cpu_usage > 90:
            status = "CRITICAL"
        elif memory_usage > 80 or disk_usage > 80 or cpu_usage > 80:
            status = "WARNING"
        
        log_health_check("system_resources", status, details)
        
        # Create or resolve alerts
        if memory_usage > 90:
            create_alert("high_memory_usage", f"Memory usage is critically high: {memory_usage}%")
        elif memory_usage > 80:
            create_alert("high_memory_usage", f"Memory usage is high: {memory_usage}%")
        else:
            resolve_alert("high_memory_usage")
            
        if disk_usage > 90:
            create_alert("high_disk_usage", f"Disk usage is critically high: {disk_usage}%")
        elif disk_usage > 80:
            create_alert("high_disk_usage", f"Disk usage is high: {disk_usage}%")
        else:
            resolve_alert("high_disk_usage")
            
        if cpu_usage > 90:
            create_alert("high_cpu_usage", f"CPU usage is critically high: {cpu_usage}%")
        elif cpu_usage > 80:
            create_alert("high_cpu_usage", f"CPU usage is high: {cpu_usage}%")
        else:
            resolve_alert("high_cpu_usage")
        
        return status, details
    except Exception as e:
        logger.error(f"Error checking system resources: {str(e)}")
        status = "ERROR"
        details = {"error": str(e)}
        log_health_check("system_resources", status, details)
        return status, details

def check_advertisement_system(db):
    """Check the advertisement system"""
    try:
        # Get counts
        ad_count = db.session.execute(text("SELECT COUNT(*) FROM advertisement")).scalar() or 0
        active_ad_count = db.session.execute(text("SELECT COUNT(*) FROM advertisement WHERE active = TRUE")).scalar() or 0
        impression_count = db.session.execute(text("SELECT COUNT(*) FROM ad_impression")).scalar() or 0
        
        # Check for recent impressions
        recent_impressions = db.session.execute(
            text("SELECT COUNT(*) FROM ad_impression WHERE timestamp > NOW() - INTERVAL '1 day'")
        ).scalar() or 0
        
        details = {
            "total_ads": ad_count,
            "active_ads": active_ad_count,
            "total_impressions": impression_count,
            "recent_impressions": recent_impressions
        }
        
        # Determine status
        status = "OK"
        
        # If we have active ads but no recent impressions, that might be an issue
        if active_ad_count > 0 and recent_impressions == 0:
            status = "WARNING"
            details["warning"] = "No recent ad impressions despite having active ads"
            create_alert("no_recent_impressions", "No recent ad impressions despite having active ads")
        else:
            resolve_alert("no_recent_impressions")
        
        log_health_check("advertisement_system", status, details)
        return status, details
    except Exception as e:
        logger.error(f"Error checking advertisement system: {str(e)}")
        status = "ERROR"
        details = {"error": str(e)}
        log_health_check("advertisement_system", status, details)
        return status, details

# Scheduled health checks
def run_health_checks(app, db):
    """Run all health checks"""
    with app.app_context():
        logger.info("Running scheduled health checks")
        check_server_status()
        check_database_connection(db)
        check_system_resources()
        check_advertisement_system(db)
        check_port_usage()

def start_health_check_scheduler(app, db, interval=300):
    """Start the health check scheduler"""
    initialize_health_db()
    logger.info(f"Starting health check scheduler with interval {interval} seconds")
    
    def scheduler_thread():
        while True:
            try:
                run_health_checks(app, db)
            except Exception as e:
                logger.error(f"Error in health check scheduler: {str(e)}")
            
            time.sleep(interval)
    
    thread = threading.Thread(target=scheduler_thread, daemon=True)
    thread.start()
    return thread

# API for health check data
def get_active_ports():
    """Get a list of all active ports and the services using them"""
    active_ports = []
    
    try:
        # Get all network connections
        connections = psutil.net_connections(kind='inet')
        
        # Process each connection to get port and associated process info
        port_process_map = {}
        for conn in connections:
            # Handle different psutil connection address formats
            if hasattr(conn.laddr, '_asdict'):  # Named tuple format
                if hasattr(conn.laddr, 'port'):
                    port = conn.laddr.port
                    pid = conn.pid
                else:
                    continue
            elif isinstance(conn.laddr, tuple) and len(conn.laddr) > 1:  # Tuple format
                port = conn.laddr[1]
                pid = conn.pid
            else:
                continue
            
            if pid and port and port not in port_process_map:
                try:
                    process = psutil.Process(pid)
                    port_process_map[port] = {
                        "pid": pid,
                        "name": process.name(),
                        "cmdline": " ".join(process.cmdline()),
                        "status": process.status(),
                        "created": datetime.datetime.fromtimestamp(process.create_time()).isoformat(),
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    port_process_map[port] = {
                        "pid": pid,
                        "name": "Unknown",
                        "cmdline": "Access denied or process no longer exists",
                        "status": "unknown",
                        "created": "unknown"
                    }
        
        # Convert the map to a sorted list
        for port, process_info in sorted(port_process_map.items()):
            active_ports.append({
                "port": port,
                "process": process_info
            })
        
    except Exception as e:
        logger.error(f"Error getting active ports: {str(e)}")
    
    return active_ports

def get_system_status(app, db):
    """Get the current system status"""
    with app.app_context():
        # Check server status
        server_status, server_details = check_server_status()
        
        # Check database connection
        db_status, db_details = check_database_connection(db)
        
        # Check system resources
        resources_status, resources_details = check_system_resources()
        
        # Check advertisement system
        ad_status, ad_details = check_advertisement_system(db)
        
        # Check port usage
        port_status, port_details = check_port_usage()
        
        # Get active ports information (legacy method, keeping for backward compatibility)
        active_ports = get_active_ports()
        
        # Determine overall status
        if 'CRITICAL' in [server_status, db_status, resources_status, ad_status, port_status]:
            overall_status = 'CRITICAL'
        elif 'WARNING' in [server_status, db_status, resources_status, ad_status, port_status]:
            overall_status = 'WARNING'
        elif 'ERROR' in [server_status, db_status, resources_status, ad_status, port_status]:
            overall_status = 'ERROR'
        else:
            overall_status = 'OK'
        
        # Get recent alerts
        alerts = get_recent_alerts(5)
        
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'overall_status': overall_status,
            'components': {
                'server': {'status': server_status, 'details': server_details},
                'database': {'status': db_status, 'details': db_details},
                'resources': {'status': resources_status, 'details': resources_details},
                'advertisement': {'status': ad_status, 'details': ad_details},
                'port_usage': {'status': port_status, 'details': port_details}
            },
            'active_ports': active_ports,
            'recent_alerts': alerts
        }

# Initialize the health monitoring system
def init_health_monitor(app, db):
    """Initialize the health monitoring system"""
    initialize_health_db()
    start_health_check_scheduler(app, db)
    logger.info("Health monitoring system initialized")