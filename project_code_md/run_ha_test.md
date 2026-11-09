# `run_ha_test.sh`

> **File:** `run_ha_test.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 15  
> **File Size:** 0.50 KB  

---

## Overview

High availability failover demonstration script testing controller fault recovery scenarios.

---

## Source Code

```bash
#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/EC499tests/run_ha_test.sh" ]; then
    exec "$SCRIPT_DIR/EC499tests/run_ha_test.sh" "$@"
fi

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

exec "${PYTHON_BIN:-python3}" "$SCRIPT_DIR/test_ha_controller_failover.py" "$@"
```
