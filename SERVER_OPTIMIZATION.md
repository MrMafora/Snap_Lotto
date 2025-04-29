# Server Performance Optimization Guide

This guide explains how to optimize the performance of the Snap Lotto application server.

## Performance Issues Identified

1. **Multiple Competing Worker Processes**: The default configuration was creating too many Gunicorn worker processes.
2. **Port Forwarding Overhead**: Using a port proxy from 5000 to 8080 added unnecessary overhead.
3. **Resource Contention**: Too many workers competing for limited CPU and memory resources.
4. **Process Management Issues**: Orphaned processes not being properly terminated.

## How to Optimize Server Performance

We've created several scripts to help improve server performance:

### Option 1: Using start_optimized_server.sh (Recommended)

This is the simplest method to optimize the server:

```bash
./start_optimized_server.sh
```

This script:
1. Kills all existing Python and Gunicorn processes
2. Starts the server with an optimized configuration
3. Binds directly to port 8080
4. Limits the number of worker processes to 2

### Option 2: Manual Start with Custom Configuration

You can manually start the server with our optimized Gunicorn configuration:

```bash
pkill -9 python
pkill -9 gunicorn
sleep 2
gunicorn -c gunicorn_optimized.conf.py main:app
```

### Option 3: Python-Based Startup

For more controlled startup with logging:

```bash
python start_optimized.py
```

## Performance Optimization Files

1. **gunicorn_optimized.conf.py**: Optimized Gunicorn configuration file
2. **start_optimized.py**: Python script to manage processes and start the server
3. **start_optimized_server.sh**: Simple shell script for easy execution
4. **restart_optimized.py**: Alternative restart script for the server

## Configuration Details

Our optimized Gunicorn configuration makes the following improvements:

1. **Limited Workers**: Only 2 worker processes instead of the default 17+
2. **Direct Port Binding**: Binds directly to port 8080 instead of using a proxy
3. **Optimized Thread Settings**: 2 threads per worker for better performance
4. **Improved Connection Handling**: Better timeout and keep-alive settings
5. **Enhanced Process Management**: Proper killing of stale processes

## Verifying Optimization

After starting the optimized server, you can verify it's running correctly:

```bash
# Check running processes (should show only 2-3 workers)
ps -ef | grep gunicorn

# Check port binding
netstat -tuln | grep 8080

# Check server logs
tail -f optimized.log
```

## Troubleshooting

If you encounter issues:

1. **Server Won't Start**: Ensure all previous Python processes are killed with `pkill -9 python`
2. **Port Already In Use**: Check which process is using port 8080 with `lsof -i :8080`
3. **Performance Issues Continue**: Try reducing worker count to 1 in gunicorn_optimized.conf.py

## Why This Matters

Optimizing the server configuration significantly improves:
- Page load times
- Application stability
- Memory usage
- CPU utilization
- Overall user experience

These optimizations are especially important for applications running in constrained environments like Replit.

---

*Note: This optimization focuses on server performance only. For database optimizations, see the separate database optimization guide.*