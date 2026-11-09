# `run_random_blind_test.sh`

> **File:** `run_random_blind_test.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 15  
> **File Size:** 0.52 KB  

---

## Overview

Zero-shot blind topology transfer evaluation automation script.

---

## Source Code

```bash
#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/EC499tests/run_random_blind_test.sh" ]; then
    exec "$SCRIPT_DIR/EC499tests/run_random_blind_test.sh" "$@"
fi

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

exec "${PYTHON_BIN:-python3}" "$SCRIPT_DIR/evaluate_random_blind_topology.py" "$@"
```
