#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔮 THE ORACLE - UI Launcher${NC}"
echo ""

# Check virtual environment
VENV_PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo -e "${RED}Error: Virtual environment not found at .venv${NC}"
    echo "Run: bash scripts/bootstrap_all.sh"
    exit 1
fi

# Kill existing processes on ports 8000 and 8080
echo "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
sleep 1

# Start API server
echo -e "${GREEN}Starting API server on port 8000...${NC}"
source .venv/bin/activate
python -c "from scripts.serve_coding_runs import main; main()" > "$ROOT/runtime/api_server.log" 2>&1 &
API_PID=$!
echo $API_PID > "$ROOT/runtime/pids/api_server.pid"

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API server ready${NC}"
        break
    fi
    sleep 0.5
done

# Start UI server
echo -e "${GREEN}Starting UI server on port 8080...${NC}"
python "$ROOT/ui/server.py" > "$ROOT/runtime/ui_server.log" 2>&1 &
UI_PID=$!
echo $UI_PID > "$ROOT/runtime/pids/ui_server.pid"

# Wait for UI to be ready
sleep 2

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🔮 THE ORACLE is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}API:${NC}   http://localhost:8000"
echo -e "  ${BLUE}UI:${NC}    http://localhost:8080"
echo ""
echo -e "  ${YELLOW}Click the UI link to open the interface${NC}"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Keep script running
trap 'echo -e "\n${RED}Stopping servers...${NC}"; kill $API_PID $UI_PID 2>/dev/null || true; exit 0' INT
wait
