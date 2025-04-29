# Performance Optimization Guide

This document explains the performance optimizations made to the Snap Lotto application and provides instructions for running the application in optimized mode.

## Performance Issues Identified

1. **Multiple Competing Processes**: The application was previously running multiple Gunicorn worker processes, creating resource contention.
2. **Port Forwarding Overhead**: Using a port proxy to forward from port 5000 to port 8080 added extra overhead.
3. **Excessive Worker Processes**: Too many worker processes were being spawned, leading to memory issues and slow response times.
4. **Process Management Issues**: Processes weren't being properly terminated, leading to orphaned processes.

## Optimization Solutions

1. **Direct Port Binding**: Bind Gunicorn directly to port 8080 instead of using port forwarding.
2. **Reduced Worker Count**: Limit the number of worker processes to 4 to prevent resource contention.
3. **Process Management**: Properly kill existing processes before starting new ones.
4. **Optimized Gunicorn Settings**: Use optimized thread and connection settings.

## Running the Optimized Server

We've created several scripts to help run the application in optimized mode:

### 1. Using run_optimized.py (Recommended)

This is the recommended approach as it handles all the optimization steps automatically:

```bash
python run_optimized.py
```

This script:
- Kills any existing Python processes
- Starts Gunicorn directly on port 8080
- Uses optimized worker and thread settings
- Provides better logging and error handling

### 2. Using optimized_server.py

For a more lightweight approach using Flask's built-in server:

```bash
python optimized_server.py
```

This runs the Flask development server directly on port 8080, which is useful for debugging but not recommended for production.

### 3. Using run_direct_server.py

Another approach that provides detailed process management:

```bash
python run_direct_server.py
```

This script manages processes and starts the optimized server with robust error handling.

## Performance Monitoring

After starting the optimized server, you can monitor its performance:

1. Check running processes:
```bash
ps -ef | grep python
```

2. Check port binding:
```bash
netstat -tuln | grep 8080
```

3. Monitor server logs:
```bash
tail -f optimized_server.log
```

## Troubleshooting

If you encounter issues:

1. **Server won't start**: Ensure all previous Python processes are terminated:
```bash
pkill -9 python
pkill -9 gunicorn
```

2. **Port already in use**: Check which process is using port 8080:
```bash
lsof -i :8080
```

3. **Slow performance**: The server might still have too many workers. Edit run_optimized.py to reduce worker_count to 2.

## Performance Impact

The optimizations should result in:
- Faster page load times
- Reduced memory usage
- More stable application performance
- Better handling of concurrent requests

For any further issues, please review the application logs or contact technical support.