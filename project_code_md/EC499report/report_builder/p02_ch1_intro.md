# `EC499report/report_builder/p02_ch1_intro.py`

> **File:** `EC499report/report_builder/p02_ch1_intro.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 79  
> **File Size:** 6.94 KB  

---

## Overview

Chapter 1: Introduction

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
# Chapter 1: Introduction

CHAPTER_1_INTRO = r'''
\chapter{Introduction}
\label{chap:introduction}

\section{Project Background and Problem}
Traffic engineering concerns the way network traffic is assigned to available routes. A shortest-path policy is straightforward to configure, but its link costs do not necessarily reflect changing traffic loads. Several transfers can therefore compete for the same link even when another route is available. The resulting queues can increase delay and packet loss. OSPF and equal-cost multipath forwarding provide established routing mechanisms, but their configured costs alone do not describe current queue occupancy or utilisation \cite{moy1998ospf}.

Software-defined networking provides a practical way to investigate alternative routing decisions. An application can collect switch counters, maintain a topology model, and install forwarding rules through a controller. The problem addressed in this project is how to implement such a system, use a trained routing policy within it, and determine when its decisions are useful compared with simpler routing methods.

\section{Project Aim and Objectives}
\label{sec:aim_objectives}
The aim is to design, implement, and evaluate a software-defined traffic-engineering prototype that selects routes using network-state information and deep reinforcement learning.

The project objectives are to:
\begin{enumerate}
    \item Build a network-state manager that maintains topology, link statistics, candidate paths, and flow information.
    \item Implement a routing agent that chooses a valid path from a bounded candidate set.
    \item Integrate the agent with a Ryu/OpenFlow controller and provide a dashboard for inspecting the system.
    \item Implement comparable shortest-path, equal-cost, widest-path, and least-loaded baselines for software-model testing.
    \item Test the software and compare routing behaviour using model-based experiments and separate Mininet packet measurements.
    \item Provide a health-checked active/standby pool and test client HTTP recovery when an endpoint fails.
\end{enumerate}

\section{Importance of the Project}
Route selection affects how effectively a network uses its existing links. An adaptive routing method may reduce congestion without increasing link capacity, but it also adds computation, training, and monitoring requirements. Comparing the learned policy with deterministic heuristics is therefore necessary: a more complicated method is useful only if its behaviour justifies that complexity.

The project also provides a teaching and testing platform. The dashboard makes route choices visible, while the scripts and saved results allow a future student to inspect the implementation and repeat the evaluation. The intended users are students and engineers investigating routing in a controlled software environment.

\section{Method and Main Project Steps}
The work was organised around implementation followed by functional and performance testing:
\begin{enumerate}
    \item Create the topology and state-management modules, including candidate-path generation and link-load accounting.
    \item Implement the dueling double deep Q-network and its prioritised replay buffer using PyTorch.
    \item Connect routing decisions to the Ryu controller's flow-rule installation path.
    \item Add the dashboard, routing baselines, and active/standby endpoint pool.
    \item Run the automated software checks and the five-topology software-model comparison.
    \item Execute the separate 120-trial Mininet experiment, retain its raw outputs, and analyse throughput, UDP datagram loss, ICMP diagnostics, and decision time.
\end{enumerate}
Chapter~\ref{chap:project} describes the final implementation and test procedures. The full source is supplied separately; supporting commands and specifications are included in the appendices.

\section{Project Scope and Deliverables}
The completed deliverables are the Python implementation, trained model, controller application, web dashboard, automated tests, experiment scripts, saved data, and this report. The evaluation covers five software-model fixtures and packet emulation on Tree and Fat-Tree networks.

The routing policy selects one of up to four loopless candidate paths. It uses ten summary features, rather than a complete graph representation. The controller pool supports local endpoint selection and HTTP retry; it does not maintain a replicated consensus log. The platform was tested on a virtualised Linux host. Hardware-switch performance, production availability, and generalisation to arbitrary networks are outside the demonstrated scope.

\section{Report Organisation}
The report follows the department's graduation-project template:
\begin{itemize}
    \item Chapter~\ref{chap:background} introduces the tools and concepts needed to understand the implementation and explains why they were chosen.
    \item Chapter~\ref{chap:related} reviews relevant earlier systems and recent work that informs the design.
    \item Chapter~\ref{chap:project} describes the project under Design, Experiments, Testing and Evaluation, and Results and Discussion.
    \item Chapter~\ref{chap:conclusion} summarises what was achieved, the usefulness of the system, and its limitations.
    \item Chapter~\ref{chap:future} identifies practical next steps based on those limitations.
\end{itemize}
References identify the external material used. The appendices contain supporting equations, API specifications, the test listing, implementation notes, and the operating manual.

Table~\ref{tab:objective_mapping} provides an explicit traceability matrix mapping each of the six project objectives defined in Section~\ref{sec:aim_objectives} to its corresponding design section, experimental evaluation, and technical appendix.

\begin{table}[htbp]
\centering
\small
\caption{Traceability Matrix Mapping Project Objectives to Dissertation Sections and Appendices.}
\label{tab:objective_mapping}
\begin{tabularx}{\linewidth}{lXp{3.8cm}p{3.2cm}}
\toprule
\textbf{Objective} & \textbf{Core Engineering Scope} & \textbf{Design \& Implementation} & \textbf{Evaluation \& Appendices} \\
\midrule
Obj.~1 & Network state manager \& 4-tier candidate routing & Section~\ref{sec:design} & Section~\ref{sec:testing}, App.~\ref{app:openflow_api} \\
Obj.~2 & D3QN routing agent with SumTree PER & Section~\ref{sec:design} & Section~\ref{sec:results}, App.~\ref{app:math_proofs} \\
Obj.~3 & Ryu OpenFlow controller \& real-time dashboard & Section~\ref{sec:design} & Section~\ref{sec:testing}, App.~\ref{app:manual} \\
Obj.~4 & Baseline routing heuristics (SPF, ECMP, WSP, LLR, MILP) & Section~\ref{sec:design}, \ref{sec:experiments} & Section~\ref{sec:results} \\
Obj.~5 & 5-topology software tournament \& 120-run Mininet emulation & Section~\ref{sec:experiments} & Section~\ref{sec:mininet_eval}, App.~\ref{app:test_suite} \\
Obj.~6 & Active/standby controller pool \& transparent HTTP failover & Section~\ref{sec:design} & Section~\ref{sec:results}, App.~\ref{app:viva_voce} \\
\bottomrule
\end{tabularx}
\end{table}
'''
```
