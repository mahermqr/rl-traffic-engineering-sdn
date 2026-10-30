# `agent/__init__.py`

> **File:** `agent/__init__.py`  
> **Subsystem / Category:** 1. Reinforcement Learning (DQN) Agent  
> **Language:** `python`  
> **Lines of Code:** 18  
> **File Size:** 0.40 KB  

---

## Overview

Reinforcement learning package export exposing DQNRoutingAgent and PrioritizedReplayBuffer.

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
"""
Intelligence Layer: Pure PyTorch Reinforcement Learning Agents for SDN Traffic Engineering (EC499).
"""

import sys
import os

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from .dqn_router import DQNRoutingAgent
from .prioritized_replay import PrioritizedReplayBuffer

__all__ = [
    'DQNRoutingAgent',
    'PrioritizedReplayBuffer'
]
```
