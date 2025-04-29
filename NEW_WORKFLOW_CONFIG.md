# Optimized Workflow Configuration

To use the optimized server configuration:

## Option 1: Manually run the optimized server

```bash
./start_optimized_server.sh
```

This will:
1. Kill all existing Python and Gunicorn processes
2. Wait for 2 seconds to ensure all processes are terminated
3. Start the optimized server using `run_optimized.py`

## Option 2: Create a new workflow (Recommended)

To create a new optimized workflow:

1. Open the Replit workflow editor
2. Create a new workflow named "Optimized Server"
3. Add the following tasks:
   - Task 1: `packager.installForAll`
   - Task 2: `shell.exec` with args `python run_optimized.py`
   - Set waitForPort to 8080

## Why this configuration is better

1. Directly binds to port 8080 (no port forwarding overhead)
2. Uses only 4 worker processes (reduced resource contention)
3. Optimized connection handling settings
4. Proper process management (no orphaned processes)

For more details, see the PERFORMANCE_OPTIMIZATION_GUIDE.md file.
