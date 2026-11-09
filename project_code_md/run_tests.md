# `run_tests.sh`

> **File:** `run_tests.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 15  
> **File Size:** 0.47 KB  

---

## Overview

Automated test execution script running the complete pytest and unittest suites.

---

## Source Code

```bash
#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/EC499tests/run_tests.sh" ]; then
    exec "$SCRIPT_DIR/EC499tests/run_tests.sh" "$@"
fi

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

exec "${PYTHON_BIN:-python3}" "$SCRIPT_DIR/test_suite.py" "$@"
```
