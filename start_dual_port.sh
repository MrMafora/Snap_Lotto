#!/bin/bash
# Start the Lottery Application with Dual Port Support
# This script handles both development and production modes

# Define colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}        Lottery Application Launcher                   ${NC}"
    echo -e "${BLUE}=======================================================${NC}"
}

print_usage() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e ""
    echo -e "Options:"
    echo -e "  --dev                  Run in development mode (port 5000 primary with 8080 bridge)"
    echo -e "  --prod                 Run in production mode (port 8080 only)"
    echo -e "  --dual                 Run in dual port mode (both ports 5000 and 8080)"
    echo -e "  --single [PORT]        Run in single port mode on the specified port"
    echo -e "  --help                 Show this help message"
    echo -e ""
}

# Parse command line arguments
MODE="auto"
PORT=""
ENVIRONMENT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            ENVIRONMENT="development"
            MODE="dual"
            shift
            ;;
        --prod)
            ENVIRONMENT="production"
            MODE="single"
            PORT="8080"
            shift
            ;;
        --dual)
            MODE="dual"
            shift
            ;;
        --single)
            MODE="single"
            if [[ $2 =~ ^[0-9]+$ ]]; then
                PORT="$2"
                shift
            else
                PORT="5000"
            fi
            shift
            ;;
        --help)
            print_banner
            print_usage
            exit 0
            ;;
        *)
            # Unknown option
            echo -e "${RED}Error: Unknown option $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Set default environment if not specified
if [ -z "$ENVIRONMENT" ]; then
    ENVIRONMENT="development"
fi

# Set default port for single mode if not specified
if [ "$MODE" == "single" ] && [ -z "$PORT" ]; then
    if [ "$ENVIRONMENT" == "production" ]; then
        PORT="8080"
    else
        PORT="5000"
    fi
fi

# Display configuration
print_banner
echo -e "${YELLOW}Starting application with the following configuration:${NC}"
echo -e "  Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "  Mode: ${GREEN}${MODE}${NC}"
if [ "$MODE" == "single" ]; then
    echo -e "  Port: ${GREEN}${PORT}${NC}"
fi
echo -e "${BLUE}=======================================================${NC}"

# Run the direct port binding script with the appropriate options
if [ "$MODE" == "single" ]; then
    echo -e "${YELLOW}Starting in single port mode...${NC}"
    python direct_port_binding.py --mode single --port "$PORT" --environment "$ENVIRONMENT"
else
    echo -e "${YELLOW}Starting in dual port mode...${NC}"
    python direct_port_binding.py --mode dual --environment "$ENVIRONMENT"
fi