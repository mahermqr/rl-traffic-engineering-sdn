# `EC499report/report_builder/p07_ch5_conclusion.py`

> **File:** `EC499report/report_builder/p07_ch5_conclusion.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 23  
> **File Size:** 2.90 KB  

---

## Overview

Chapter 5: Conclusion

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
# Chapter 5: Conclusion

CHAPTER_5_CONCLUSION = r'''
\chapter{Conclusion}
\label{chap:conclusion}

\section{Work Completed}
The project developed a software-defined traffic-engineering prototype that combines network-state monitoring, candidate-path generation, a trained routing agent, and OpenFlow rule installation. The implementation also includes routing baselines, a web dashboard, automated tests, and an active/standby controller-endpoint pool. The resulting system provides a practical environment for inspecting route choices and repeating controlled comparisons.

The work met the implementation objectives by connecting the learning components to the controller and providing saved test outputs. The 42 automated checks passed for the behaviours covered by the suite, and the packet experiment completed all 120 scheduled conditions. These checks support the operation of the prototype within its tested software environment.

\section{Main Results and Usefulness}
The final five-topology software-model comparison reports mean sampled path-bottleneck utilisation of 30.80\% for D3QN and 66.80\% for the OSPF-style baseline. Mean modelled delay changes from 158.34 to 44.50~ms. These results show that the implemented policy can select useful alternative routes within the model, although its performance varies by topology and metric.

The separate packet measurements give a more mixed result. Tree TCP throughput averages 34.08~Mbps for D3QN, 28.56~Mbps for SPF, and 38.09~Mbps for least-loaded routing. On Fat-Tree UDP, D3QN has a modest datagram-loss advantage over SPF, while the least-loaded heuristic remains competitive. The confidence intervals and detailed comparisons are reported in Chapter~\ref{chap:project}. The practical lesson is that a trained policy should be assessed against simple load-aware methods for the intended workload.

The recovery tests separately demonstrate local standby selection and client HTTP retry. The reported 0.001~ms bookkeeping observation and 37.96~ms client-recovery observation describe different operations; neither establishes uninterrupted packet forwarding.

\section{Limitations}
The results are limited to software models and packet emulation on a virtualised host. The route selector uses ten summary features and at most four candidates, so it cannot represent every possible network state or route. Modelled jitter and loss must be distinguished from iperf and ICMP measurements. In addition, the fixed-duration background stream can finish before the measured packet transfer ends.

The endpoint pool does not maintain consistent replicated controller state, and its HTTP tests do not measure OpenFlow reconnection or packet continuity. Hardware-switch performance, production availability, and arbitrary-topology generalisation remain unverified. Within these limits, the project delivers a working platform, repeatable procedures, and recorded results that can support further development.
'''
```
