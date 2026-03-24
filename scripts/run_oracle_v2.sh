#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🔮 THE ORACLE v2.0 - Single Coherent System${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check virtual environment
VENV_PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo -e "${RED}Error: Virtual environment not found at .venv${NC}"
    echo "Run: bash scripts/bootstrap_all.sh"
    exit 1
fi

# Clean up existing processes
echo "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start API server
echo -e "${GREEN}Starting Oracle v2.0 API server on port 8000...${NC}"
source .venv/bin/activate

# Use the new server
python -c "from oracle_runtime.api.server import main; main()" > "$ROOT/runtime/oracle_v2.log" 2>&1 &
API_PID=$!
echo $API_PID > "$ROOT/runtime/pids/oracle_v2.pid"

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API server ready${NC}"
        break
    fi
    sleep 0.5
done

# Check readiness
echo "Checking system readiness..."
READY=$(curl -s http://localhost:8000/ready 2>/dev/null || echo '{"status": "error"}')

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🔮 THE ORACLE v2.0 is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}API:${NC}     http://localhost:8000"
echo -e "  ${BLUE}Health:${NC}   http://localhost:8000/health"
echo -e "  ${BLUE}Status:${NC}   http://localhost:8000/system/status"
echo ""
echo -e "  ${YELLOW}Execution Spine:${NC}"
echo -e "    Intent → Planner → Command → Verified Executor → Events → Commit"
echo ""
echo -e "  ${YELLOW}Single Authority:${NC} VerifiedExecutor"
echo -e "  ${YELLOW}Event Store:${NC}    Append-only (events.log)"
echo -e "  ${YELLOW}State:${NC}          Projected (state.json)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Keep script running
trap 'echo -e "\n${RED}Stopping Oracle v2.0...${NC}"; kill $API_PID 2>/dev/null || true; exit 0' INT
wait
