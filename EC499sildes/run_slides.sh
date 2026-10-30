#!/usr/bin/env bash
# ==============================================================================
# EC499 Final Defense Presentation Launcher
# Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network
# Candidate: Maher Alqadhi (ID: 2210249576) | Supervisor: Dr. Suad El-Geder
# ==============================================================================

set -e
SLIDES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8099

echo "========================================================================"
echo "  🎓 EC499 GRADUATION PROJECT DEFENSE SLIDES"
echo "  Reinforcement Learning for Adaptive Traffic Engineering in SDN"
echo "========================================================================"
echo ""
echo "  [1] Master Interactive Web Deck : ${SLIDES_DIR}/index.html"
echo "  [2] High-Definition PowerPoint  : ${SLIDES_DIR}/EC499_Final_Defense_Presentation.pptx (32 Slides)"
echo "  [3] Exported Vector PDF Deck    : ${SLIDES_DIR}/EC499_Defense_Slides.pdf (32 Pages)"
echo ""
echo "------------------------------------------------------------------------"
echo "  Keyboard Controls:"
echo "    [Space] / [→] : Next slide"
echo "    [←]           : Previous slide"
echo "    [F]           : Toggle Fullscreen"
echo "    [P]           : Open Presenter Mode (with Stopwatch & Speaker Notes)"
echo "    [O] / [Esc]   : Slide Overview Grid"
echo "    [M] / [T]     : Toggle Cyber Dark / Academic Light Theme"
echo "    [L]           : Toggle Laser Pointer"
echo "    [B]           : Blank Screen"
echo "------------------------------------------------------------------------"

# Launch local HTTP server in background
echo "⚡ Starting local slides presentation server on http://127.0.0.1:${PORT}..."
/home/maher/Downloads/EC499t/.venv/bin/python3 -m http.server ${PORT} --directory "${SLIDES_DIR}" >/dev/null 2>&1 &
SERVER_PID=$!

trap "kill $SERVER_PID 2>/dev/null || true; exit 0" INT TERM EXIT

sleep 0.8

# Open in Chrome / default browser
if [ -x "/home/maher/.local/bin/google-chrome" ]; then
    echo "🌐 Opening in Google Chrome..."
    /home/maher/.local/bin/google-chrome "http://127.0.0.1:${PORT}/index.html" &
elif which xdg-open >/dev/null 2>&1; then
    echo "🌐 Opening with xdg-open..."
    xdg-open "http://127.0.0.1:${PORT}/index.html" &
fi

echo ""
echo "✅ Presentation is running at http://127.0.0.1:${PORT}/index.html"
echo "   Press Ctrl+C to stop the server."
echo "========================================================================"

wait $SERVER_PID
