#!/usr/bin/env bash
# ==============================================================================
# Master Reproducibility Suite (EC499 - University of Tripoli)
# Candidate: Maher Abdulnasir Alqadhi (ID: 2210249576)
# Supervisor: Dr. Suad El-Geder
#
# Usage:
#   bash reproduce_all.sh              # Fast mode: runs unit tests, verifies datasets, regenerates figures, compiles LaTeX report, builds package
#   bash reproduce_all.sh --rerun      # Full rerun: retrains all ablation models, sweeps seeds, solves MILP oracle, regenerates everything
#   bash reproduce_all.sh --test-only  # Run 42-test unit and regression suite
#   bash reproduce_all.sh --pdf-only   # Recompile LaTeX report only
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Text styles
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

log_info() {
    echo -e "${CYAN}[INFO]${RESET} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${RESET} $1"
}

log_step() {
    echo -e "\n${BOLD}${YELLOW}>>> STAGE: $1${RESET}"
}

# 1. Environment Detection
log_step "1. Detecting Python & TeX Environment"
if [ -n "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ]; then
    : # Keep user PYTHON_BIN
elif [ -x "$HOME/ec499_env/bin/python" ]; then
    PYTHON_BIN="$HOME/ec499_env/bin/python"
elif [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    PYTHON_BIN="python"
fi

log_info "Python interpreter: $PYTHON_BIN"
"$PYTHON_BIN" -c "import torch, scipy, networkx, matplotlib; print(f'  PyTorch {torch.__version__}, SciPy {scipy.__version__}, NetworkX {networkx.__version__}, Matplotlib {matplotlib.__version__}')"

if command -v tectonic >/dev/null 2>&1; then
    TECTONIC_BIN="$(command -v tectonic)"
    log_info "Tectonic LaTeX compiler: $TECTONIC_BIN"
else
    TECTONIC_BIN=""
    log_info "Tectonic compiler not found; will look for pdflatex."
fi

# Handle quick arguments
if [ "$1" == "--test-only" ]; then
    log_step "Running Test Suite Only"
    "$PYTHON_BIN" test_suite.py
    exit 0
fi

if [ "$1" == "--pdf-only" ]; then
    log_step "Compiling LaTeX Report Only"
    cd "$SCRIPT_DIR/report_artifacts"
    if [ -n "$TECTONIC_BIN" ]; then
        "$TECTONIC_BIN" main.tex
    else
        pdflatex -interaction=nonstopmode main.tex
    fi
    log_success "Report generated: report_artifacts/main.pdf ($(ls -lh main.pdf | awk '{print $5}'))"
    exit 0
fi

# 2. Regression Test Suite
log_step "2. Running 42-Test Unit & System Regression Suite"
"$PYTHON_BIN" test_suite.py
log_success "All unit and integration regression tests passed cleanly."

# 3. Phase 1 Experimental Suite
log_step "3. Phase 1 Experimental Suite (Ablation, Seeds, Held-Out, Oracle, Sensitivity)"
DATA_DIR="$SCRIPT_DIR/report_artifacts/data"
mkdir -p "$DATA_DIR"

RUN_PHASE1=false
if [ "$1" == "--rerun" ] || [ ! -f "$DATA_DIR/ablation_study_results.json" ] || [ ! -f "$DATA_DIR/optimisation_oracle_results.json" ]; then
    RUN_PHASE1=true
fi

if [ "$RUN_PHASE1" = true ]; then
    log_info "Executing experiment_phase1_suite.py (Comprehensive ablation, multi-seed, OOD held-out, MILP oracle, sensitivity)..."
    "$PYTHON_BIN" experiment_phase1_suite.py
    log_success "Phase 1 experiments completed and datasets generated."
else
    log_info "Phase 1 datasets already cached in report_artifacts/data/. (Pass --rerun to re-execute full training sweeps)"
    for f in ablation_study_results.json multiple_model_seeds_results.json held_out_topologies_results.json optimisation_oracle_results.json reward_sensitivity_retraining_results.json; do
        if [ -f "$DATA_DIR/$f" ]; then
            log_info "  Found cached dataset: $f ($(wc -c < "$DATA_DIR/$f") bytes)"
        else
            log_info "  Missing $f; executing Phase 1 suite..."
            "$PYTHON_BIN" experiment_phase1_suite.py
            break
        fi
    done
fi

# 4. Phase 2 Packet-Level Validation
log_step "4. Phase 2 Packet-Level Validation (M/M/1/K Breakdown & Link Failover Dynamics)"
RUN_PHASE2=false
if [ "$1" == "--rerun" ] || [ ! -f "$DATA_DIR/queue_model_validation_results.json" ]; then
    RUN_PHASE2=true
fi

if [ "$RUN_PHASE2" = true ]; then
    log_info "Executing experiment_phase2_packet_validation.py..."
    "$PYTHON_BIN" experiment_phase2_packet_validation.py
    log_success "Phase 2 packet-level queue simulation completed."
else
    log_info "Phase 2 dataset already cached: queue_model_validation_results.json"
fi

# 5. Publication Figure Generation
log_step "5. Generating Publication Figures (300 DPI)"
FIG_DIR="$SCRIPT_DIR/report_artifacts/figures"
mkdir -p "$FIG_DIR"
"$PYTHON_BIN" generate_phase1_figures.py
log_success "Generated all 6 publication figures in report_artifacts/figures/:"
ls -lh "$FIG_DIR"/*.png | awk '{print "  " $9 " (" $5 ")"}'

# 6. LaTeX Report Compilation
log_step "6. Compiling Authoritative Master Report (report_artifacts/main.tex)"
cd "$SCRIPT_DIR/report_artifacts"
if [ -n "$TECTONIC_BIN" ]; then
    "$TECTONIC_BIN" main.tex
elif command -v pdflatex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode main.tex
    bibtex main || true
    pdflatex -interaction=nonstopmode main.tex
    pdflatex -interaction=nonstopmode main.tex
else
    echo -e "${RED}[WARNING]${RESET} Neither tectonic nor pdflatex was found. Skipping PDF compilation."
fi

if [ -f "$SCRIPT_DIR/report_artifacts/main.pdf" ]; then
    PDF_SIZE=$(ls -lh "$SCRIPT_DIR/report_artifacts/main.pdf" | awk '{print $5}')
    log_success "Master LaTeX Report successfully compiled: report_artifacts/main.pdf ($PDF_SIZE)"
    # Keep docs copy in sync
    cp -f "$SCRIPT_DIR/report_artifacts/main.pdf" "$SCRIPT_DIR/docs/Project_Report_EC499_Final.pdf"
    log_info "Synchronized docs/Project_Report_EC499_Final.pdf"
fi
cd "$SCRIPT_DIR"

# 7. Graduation Packaging
log_step "7. Packaging Authoritative Graduation Bundle"
"$PYTHON_BIN" package_submission.py
log_success "Graduation package successfully built and verified."

echo -e "\n${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}  REPRODUCIBILITY RUN COMPLETED SUCCESSFULLY!                         ${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "Authoritative Artifacts:"
echo -e "  - Compiled Master Report: ${CYAN}report_artifacts/main.pdf${RESET}"
echo -e "  - Experimental Datasets:  ${CYAN}report_artifacts/data/*.json${RESET}"
echo -e "  - Publication Figures:    ${CYAN}report_artifacts/figures/*.png${RESET}"
echo -e "  - Graduation Archive:     ${CYAN}dist/Maher_Alqadhi_2210249576_EC499_Final_Graduation_Submission.zip${RESET}"
echo -e "  - Viva Defense Guide:     ${CYAN}docs/VIVA_DEFENSE_MASTER_GUIDE.md${RESET}\n"
