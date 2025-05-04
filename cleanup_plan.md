# Project Cleanup Plan

This document outlines files that can be safely archived to reduce clutter in the main project directory.

## Port-Related Solutions (move to archived_scripts/port_solutions)

These files were created to solve port forwarding issues, but we're now using only one solution:

- both_ports.py (redundant - we're using new_port_proxy.py)
- port_forward.py (redundant - we're using new_port_proxy.py)
- port_proxy.py (older version of proxy)
- proxy_only.py (redundant)
- simple_proxy.py (redundant)
- start_on_port_8080.py (redundant)
- run_on_port_8080.sh (redundant shell script)
- run_server_port_8080.sh (redundant shell script)
- start_with_proxy.sh (redundant shell script)

## One-Time Scripts (move to archived_scripts/one_time_scripts)

These scripts were used for one-time operations and are no longer needed in regular use:

- add_lotto_2534.py (one-time fix for specific draw)
- check_draw_2534.py (one-time check script)
- import_lotto_2534.py (one-time import script)
- count_screenshots.py (utility script, not part of core functionality)
- create_admin.py (one-time script to create admin user)
- purge_data.py (utility for clearing data, keep in archive for potential future use)

## Test Scripts (move to archived_scripts/test_scripts)

These scripts were created for testing and debugging:

- test_api_access.py
- test_api_endpoints.py
- test_csrf_fetch.py
- test_lottery_analysis_ui.py
- test_server.py

## Documentation Consolidation

Consider consolidating related .md files into a single documentation repository or directory.

## Important Note

These files are moved to archived directories rather than deleted entirely. If needed, they can be accessed from their archive locations.