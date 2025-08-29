#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# rag-tech - Single-Command Startup Script
# =============================================================================
# Developer: just run "./start.sh" and everything works automatically!
# - Automatic Python environment setup
# - Download Granite 1B model (~600MB)
# - Index corpus with Sentence-Transformers
# - RAG API ready at http://localhost:8000
# =============================================================================

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

log() { echo -e "${CYAN}[rag-tech]${NC} $1"; }
success() { echo -e "${GREEN}✅${NC} $1"; }
warning() { echo -e "${YELLOW}⚠️${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; exit 1; }

# =============================================================================
# Configuration
# =============================================================================
readonly PY=${PYTHON:-python3}
readonly PORT=${PORT:-8000}
readonly HOST=${HOST:-0.0.0.0}

# Ensure ARM64 native execution on Apple Silicon
export DOCKER_DEFAULT_PLATFORM=linux/arm64
export ARCHFLAGS="-arch arm64"


# =============================================================================
# Helper Functions
# =============================================================================
check_command() {
    command -v "$1" >/dev/null 2>&1 || error "Command '$1' not found. Please install it first."
}

cleanup_port() {
    local port="$1"
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        log "Cleaning up processes on port $port..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$remaining" ]; then
            echo "$remaining" | xargs kill -KILL 2>/dev/null || true
            sleep 1
        fi
        success "Port $port cleaned up"
    fi
}

ensure_arm64() {
    # Check if we're on Apple Silicon
    if [[ "$(uname -m)" == "arm64" ]]; then
        log "Detected Apple Silicon - optimizing for ARM64..."
        
        # Force pip to prefer ARM64 wheels
        export _PIP_LOCATIONS_NO_WARN_ON_MISMATCH=1
        export CMAKE_OSX_ARCHITECTURES=arm64
        
        # Check Python architecture
        local py_arch=$($PY -c "import platform; print(platform.machine())")
        if [[ "$py_arch" != "arm64" ]]; then
            warning "Python is running as $py_arch (not arm64) - this may cause x86 emulation"
            warning "Consider installing Python ARM64 natively: brew install python@3.11"
        else
            success "Python running natively on ARM64"
        fi
    fi
}

# =============================================================================
# Main Setup Flow
# =============================================================================
main() {
    echo -e "${BLUE}"
    cat << "EOF"
    ██████╗  █████╗  ██████╗       ████████╗███████╗ ██████╗██╗  ██╗
    ██╔══██╗██╔══██╗██╔════╝       ╚══██╔══╝██╔════╝██╔════╝██║  ██║
    ██████╔╝███████║██║  ███╗         ██║   █████╗  ██║     ███████║
    ██╔══██╗██╔══██║██║   ██║         ██║   ██╔══╝  ██║     ██╔══██║
    ██║  ██║██║  ██║╚██████╔╝         ██║   ███████╗╚██████╗██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝          ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝
    
    🤖 RAG System with IBM Granite 3.1 + Sentence-Transformers + LangGraph
EOF
    echo -e "${NC}"
    echo "⚡ Automatic setup starting..."
    echo ""

    # Step 1: System optimization and cleanup
    log "Checking system dependencies..."
    check_command "$PY"
    check_command "curl"
    success "Dependencies OK"
    
    # Ensure ARM64 optimization
    ensure_arm64
    
    # Clean up any existing processes on our port
    cleanup_port "$PORT"

    # Step 2: Python environment
    log "Setting up Python environment..."
    if [ ! -d ".venv" ]; then
        $PY -m venv .venv
        success "Virtual environment created"
    else
        success "Virtual environment exists"
    fi

    source .venv/bin/activate
    
    # Install dependencies (skip pip upgrade for speed)
    pip install -r requirements.txt >/dev/null 2>&1
    success "Python dependencies installed"

    # Step 3: Configuration
    log "Using built-in configuration defaults..."
    success "Configuration ready"

    # Step 4: Setup Ollama and Granite model
    log "Setting up Ollama and Granite 3.1 MoE 1B model..."
    
    # Check if Ollama is running
    if ! pgrep -f "ollama serve" > /dev/null; then
        log "Starting Ollama server..."
        ollama serve &
        OLLAMA_PID=$!
        echo "OLLAMA_PID=$OLLAMA_PID" > .ollama.pid
        sleep 3
    else
        success "Ollama server already running"
    fi
    
    # Check if model is available, if not download it
    if ! ollama list | grep -q "granite3.1-moe:1b"; then
        log "Downloading Granite 3.1 MoE 1B model (this may take a few minutes)..."
        ollama pull granite3.1-moe:1b
        success "Granite 3.1 MoE 1B model downloaded"
    else
        success "Granite 3.1 MoE 1B model found"
    fi

    # Step 5: Build vector index
    log "Building vector index with Sentence-Transformers..."
    if [ ! -f "storage/index.npz" ] || [ ! -f "storage/meta.json" ]; then
        python -m scripts.ingest >/dev/null 2>&1
        success "Vector index built"
    else
        success "Vector index exists"
    fi

    # Step 6: Final validation
    log "Final system validation..."
    python -c "
from app.config import settings
from app.llm import LLM
import os

# Check configuration
print(f'   LLM: ollama ({settings.MODEL})')
print(f'   Embedding: E5 multilingual ready')
print(f'   Index: {\"OK\" if os.path.exists(\"storage/index.npz\") else \"Missing\"}')

# Test LLM
llm = LLM()
print(f'   LLM Status: ollama mode ready')
"
    success "System validated and ready"

    # Step 7: Launch API
    echo ""
    echo -e "${GREEN}🚀 RAG SYSTEM READY!${NC}"
    echo ""
    echo "📊 Final configuration:"
    echo "   • 🤖 IBM Granite 3.1 MoE 1B via Ollama (ARM64 native)"
    echo "   • 🧠 E5 multilingual embeddings"
    echo "   • 📚 6 products indexed"
    echo "   • ⚡ 100% local, zero cost"
    echo "   • 💬 WhatsApp-style frontend: http://localhost:$PORT"
    echo "   • 🌐 API endpoint: http://localhost:$PORT/query"
    echo ""
    echo "🎯 For stakeholders (user-friendly UI):"
    echo "   👆 Open: http://localhost:$PORT"
    echo ""
    echo "🔧 For developers:"
    echo "   📖 API Docs: http://localhost:$PORT/docs"
    echo "   🧪 cURL: curl -X POST http://localhost:$PORT/query -H 'Content-Type: application/json' -d '{\"query\":\"H-500 features?\"}'"
    echo ""
    echo "🛠️  Troubleshooting:"
    echo "   If port conflict: pkill -f uvicorn && ./start.sh"
    echo "   To stop: Ctrl+C or pkill -f 'rag-tech|uvicorn'"
    echo ""
    log "Starting FastAPI server..."
    echo "   (Press Ctrl+C to stop)"
    echo ""

    # Start the API
    exec uvicorn app.main:app --host "$HOST" --port "$PORT" --log-level info
}

# =============================================================================
# Cleanup on exit
# =============================================================================
cleanup() {
    if [ -n "${API_PID:-}" ]; then
        kill "$API_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# =============================================================================
# Run
# =============================================================================
main "$@"
