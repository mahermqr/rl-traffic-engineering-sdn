# `scripts/resolve_python.sh`

> **File:** `scripts/resolve_python.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 37  
> **File Size:** 0.98 KB  

---

## Overview

Environment resolution script locating the appropriate Python virtual environment and Ryu dependencies.

---

## Source Code

```bash
#!/usr/bin/env bash
# Shared Python interpreter discovery for repository launchers.
# Callers may set PYTHON_BIN or VENV_PATH to override discovery.

if [[ -n "${PYTHON_BIN:-}" && -x "$PYTHON_BIN" ]]; then
    return 0
fi

python_candidates=()
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    python_candidates+=("$VIRTUAL_ENV/bin/python")
fi
if [[ -n "${VENV_PATH:-}" ]]; then
    python_candidates+=("$VENV_PATH/bin/python")
fi
python_candidates+=(
    "$SCRIPT_DIR/.venv/bin/python"
    "$SCRIPT_DIR/venv/bin/python"
    "$HOME/ec499_env/bin/python"
    "$HOME/.venv/bin/python"
)

for python_candidate in "${python_candidates[@]}"; do
    if [[ -x "$python_candidate" ]]; then
        PYTHON_BIN="$python_candidate"
        return 0
    fi
done

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "Error: no Python interpreter found. Set PYTHON_BIN explicitly." >&2
    return 1
fi
```
