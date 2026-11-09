# `controller/__init__.py`

> **File:** `controller/__init__.py`  
> **Subsystem / Category:** 2. SDN Controller Architecture & Modules  
> **Language:** `python`  
> **Lines of Code:** 14  
> **File Size:** 0.27 KB  

---

## Overview

SDN control plane package initialization for OpenFlow 1.3 Ryu applications.

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
"""
Control Plane: OpenFlow 1.3 Ryu Applications & State Management
"""

import sys
import os

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from .state_manager import StateManager

__all__ = ['StateManager']
```
