# `run_tests.sh`

> **File:** `run_tests.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 13  
> **File Size:** 0.43 KB  

---

## Overview

Automated test execution script running the complete pytest and unittest suites.

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

# shellcheck source=scripts/resolve_python.sh
source "$SCRIPT_DIR/scripts/resolve_python.sh"

exec "$PYTHON_BIN" test_suite.py "$@"
```
