# `run_ha_test.sh`

> **File:** `run_ha_test.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 13  
> **File Size:** 0.48 KB  

---

## Overview

High availability failover demonstration script testing controller fault recovery scenarios.

---

## Source Code

```bash
#!/usr/bin/env bash
# ==============================================================================
# Run High Availability 3-Controller Failover & Validation Suite (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# shellcheck source=scripts/resolve_python.sh
source "$SCRIPT_DIR/scripts/resolve_python.sh"

exec "$PYTHON_BIN" test_ha_controller_failover.py "$@"
```
