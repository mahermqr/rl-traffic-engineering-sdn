# `EC499tests/run_tests.sh`

> **File:** `EC499tests/run_tests.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 16  
> **File Size:** 0.56 KB  

---

## Overview

============================================================================== Run Unit and Integration Test Suite (EC499) ==============================================================================

---

## Source Code

```bash
#!/usr/bin/env bash
# ==============================================================================
# Run Unit and Integration Test Suite (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

exec "$PYTHON_BIN" test_suite.py "$@"
```
