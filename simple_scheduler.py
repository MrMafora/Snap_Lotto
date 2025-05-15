"""
Simple scheduler for managing background tasks in the Lottery App

This module provides a simpler, more reliable approach to scheduling
tasks in the application, such as screenshot captures, without the 
complexity of larger scheduler libraries.
"""

import threading
import time
from datetime import datetime, timedelta
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global container for scheduled tasks
scheduled_tasks = {}
stop_event = threading.Event()

def initialize_scheduler():
    """Initialize the scheduler system"""
    global stop_event
    stop_event.clear()
    logger.info("Simple scheduler initialized")

def shutdown_scheduler():
    """Shutdown all scheduler threads"""
    global stop_event
    stop_event.set()
    logger.info("Scheduler shutdown initiated")

def schedule_task(task_id, func, interval_minutes=60, args=None, kwargs=None):
    """
    Schedule a task to run at regular intervals
    
    Args:
        task_id (str): Unique identifier for the task
        func (callable): Function to call
        interval_minutes (int): Minutes between executions
        args (list, optional): Positional arguments for the function
        kwargs (dict, optional): Keyword arguments for the function
    
    Returns:
        bool: Success status
    """
    if task_id in scheduled_tasks:
        logger.warning(f"Task {task_id} is already scheduled")
        return False
    
    args = args or []
    kwargs = kwargs or {}
    
    def task_runner():
        next_run = datetime.now()
        
        while not stop_event.is_set():
            # Check if it's time to run
            if datetime.now() >= next_run:
                try:
                    logger.info(f"Running scheduled task: {task_id}")
                    func(*args, **kwargs)
                    logger.info(f"Task {task_id} completed successfully")
                except Exception as e:
                    logger.error(f"Error in scheduled task {task_id}: {str(e)}")
                
                # Calculate next run time
                next_run = datetime.now() + timedelta(minutes=interval_minutes)
                logger.info(f"Next run for {task_id}: {next_run}")
            
            # Sleep for a short time to avoid high CPU usage
            time.sleep(10)
    
    # Create and start the thread
    thread = threading.Thread(target=task_runner, daemon=True)
    scheduled_tasks[task_id] = {
        'thread': thread,
        'interval': interval_minutes,
        'func': func,
        'args': args,
        'kwargs': kwargs,
        'last_run': None,
        'next_run': datetime.now() + timedelta(minutes=interval_minutes),
        'status': 'scheduled'
    }
    
    thread.start()
    logger.info(f"Scheduled task {task_id} to run every {interval_minutes} minutes")
    return True

def get_task_status(task_id):
    """Get the status of a scheduled task"""
    if task_id not in scheduled_tasks:
        return None
    
    task = scheduled_tasks[task_id]
    return {
        'task_id': task_id,
        'interval': task['interval'],
        'last_run': task['last_run'],
        'next_run': task['next_run'],
        'status': task['status'],
        'running': task['thread'].is_alive()
    }

def get_all_task_statuses():
    """Get status of all scheduled tasks"""
    result = {}
    for task_id in scheduled_tasks:
        result[task_id] = get_task_status(task_id)
    return result

def run_task_now(task_id):
    """
    Manually trigger a scheduled task to run immediately
    
    Args:
        task_id (str): ID of the task to run
        
    Returns:
        bool: Success status
    """
    if task_id not in scheduled_tasks:
        logger.warning(f"Task {task_id} not found")
        return False
    
    task = scheduled_tasks[task_id]
    
    try:
        task['status'] = 'running'
        task['func'](*task['args'], **task['kwargs'])
        task['last_run'] = datetime.now()
        task['status'] = 'completed'
        logger.info(f"Manually triggered task {task_id} completed successfully")
        return True
    except Exception as e:
        task['status'] = 'failed'
        logger.error(f"Error running task {task_id} manually: {str(e)}")
        return False

def cancel_task(task_id):
    """
    Cancel a scheduled task
    
    Args:
        task_id (str): ID of the task to cancel
        
    Returns:
        bool: Success status
    """
    if task_id not in scheduled_tasks:
        logger.warning(f"Task {task_id} not found")
        return False
    
    # We can't actually stop the thread directly in Python,
    # but we can mark it as cancelled and the stop_event will
    # eventually cause it to exit
    scheduled_tasks[task_id]['status'] = 'cancelled'
    logger.info(f"Task {task_id} marked as cancelled")
    return True