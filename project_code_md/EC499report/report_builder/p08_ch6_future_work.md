# `EC499report/report_builder/p08_ch6_future_work.py`

> **File:** `EC499report/report_builder/p08_ch6_future_work.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 27  
> **File Size:** 2.91 KB  

---

## Overview

Chapter 6: Future Work

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
# Chapter 6: Future Work

CHAPTER_6_FUTURE_WORK = r'''
\chapter{Future Work}
\label{chap:future}

Further work should first improve measurement and reproducibility, then extend the routing and recovery functions. The following steps follow directly from the limitations of the completed project.

\section{Improve the Packet-Test Procedure}
The background traffic should be kept active throughout the measured transfer and stopped only after the measurement completes. A new run should record overlap times, the active TCP congestion-control algorithm, TCP retransmissions, and packet traces where appropriate. The existing results should remain archived so that changes to the procedure can be compared openly rather than overwriting the original evidence.

More traffic pairs, offered-load levels, queue settings, and trial durations would help establish where each policy performs well. Repeating the experiment on another host would also show how much the virtual machine and its processor scheduling affect the observations.

\section{Make Installation and Reproduction Easier}
The controller and scientific environments should have separately pinned dependencies and a documented clean-install procedure. An automated check should confirm interpreters, package imports, switch connectivity, and checkpoint compatibility before starting the full trial matrix. Tables and figures should be generated directly from the selected run manifest to reduce transcription errors.

\section{Improve Route Selection and Comparison}
The current four-candidate representation can miss useful alternatives or map different network states to similar feature vectors. Further work could compare other candidate-generation methods, reward settings, and graph-based representations. Each change should be tested against the same SPF and least-loaded baselines, with matched workloads and clearly identified training and test sets.

Capacity-aware admission checks are another practical extension. They should report explicitly when no candidate can accommodate a demand rather than treating the reward penalty as a safety guarantee.

\section{Extend Controller-Recovery Testing}
The next recovery test should measure packet behaviour during controller failure, expiry of installed rules, setup of new flows, and restoration of telemetry. A design for consistent controller state and switch-role ownership would be needed before extending the endpoint pool into a replicated control service. These functions should be implemented and tested separately from client HTTP retry.

\section{Evaluate Additional Forwarding Platforms}
After the software procedure is stable, the controller could be tested with a hardware switch. A later P4/telemetry implementation could provide additional queue information, but would require a new interface, suitable equipment, and its own validation. Results from the present Open vSwitch testbed should not be assumed to transfer directly to those platforms.
'''
```
