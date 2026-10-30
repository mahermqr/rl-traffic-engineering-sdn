# Chapter 3: Related Work

CHAPTER_3_RELATED = r'''% ============================================================================
% CHAPTER 3: RELATED WORK
% ============================================================================
\chapter{Related Work}
\label{chap:related}

\section{Overview and Taxonomy of Traffic Engineering}
Traffic Engineering (TE) has evolved across three major technological paradigms:
\begin{enumerate}
    \item \textbf{Distributed Classical Heuristics (1990--2005):} Protocols such as OSPF, IS-IS, and early MPLS-TE operated distributed routing computations with static administrative weights.
    \item \textbf{Centralized SDN Optimization (2008--2016):} Decoupled control planes enabled centralized linear solvers (e.g., Hedera \cite{al2010hedera}, Google B4 \cite{jain2013b4}, Microsoft SWAN \cite{hong2013achieving}).
    \item \textbf{Learning-Driven and AI-Based TE (2017--Present):} Machine learning, deep reinforcement learning, and graph neural networks deployed for autonomous routing adaptation.
\end{enumerate}

\section{Classical Heuristic and Static Metric Optimization}
The earliest formalization of IP traffic engineering focused on optimizing static OSPF/IS-IS link metrics. Fortz and Thorup \cite{fortz2000internet, fortz2002optimizing} proved that optimizing link weights to minimize a piecewise-linear convex congestion function is NP-hard. They proposed local search heuristics to tune static weights. However, static weight tuning assumes quasi-static traffic matrices; under dynamic microbursts, static weights cannot adapt, inducing severe localized bottlenecks.

Equal-Cost Multi-Path (ECMP) \cite{moy1998ospf} hashes packet 5-tuples (source IP, destination IP, protocol, source port, destination port) across paths with identical administrative cost. However, ECMP cannot route traffic over paths with even one additional hop, leaving viable edge-disjoint paths unused. Furthermore, hash collisions between long-lived ``elephant flows'' cause persistent link saturation and packet drops.

\section{Centralized SDN Heuristics and Linear Solvers}
The emergence of OpenFlow \cite{lanzisera2010openflow} enabled centralized global visibility. Al-Fares et al. introduced \textbf{Hedera} \cite{al2010hedera}, a dynamic flow management system for multi-rooted Fat-Tree datacenter topologies. Hedera monitors flow rates on edge switches and dynamically computes multi-commodity flow allocations for flows exceeding $10\%$ of link capacity using a greedy heuristic. However, Hedera relies on heuristic path hunting that does not learn from historical traffic dynamics.

Google deployed \textbf{B4} \cite{jain2013b4}, a private software-defined WAN connecting global datacenters. B4 employs centralized Traffic Engineering servers that solve linear programs periodically (every few minutes) to allocate bandwidth based on application priority classes. Similarly, Microsoft developed \textbf{SWAN} \cite{hong2013achieving}, which coordinates inter-datacenter transfers using centralized constrained optimization. While effective for predictable bulk transfers, the solver latency of linear programs (spanning tens of seconds to several minutes) renders them incapable of reacting to sub-second microbursts or transient localized buffer bloat.

\section{Deep Reinforcement Learning in Network Routing}
In recent years, deep reinforcement learning has been explored for network routing:
\begin{itemize}
    \item \textbf{Stampa et al. (2017):} \cite{stampa2017deep} introduced a standard Deep Q-Network (DQN) for SDN routing optimization, demonstrating delay reduction on a 14-node network. However, their system utilized a standard flat DQN (suffering from overestimation bias), uniform experience replay, and an unpenalized reward function that neglected packet loss and jitter.
    \item \textbf{Valadarsky et al. (2017):} \cite{valadarsky2017learning} proposed DRL-TE, applying policy gradient methods to optimize split ratios. However, their action space scaled combinatorially with network size, preventing convergence on larger topologies.
    \item \textbf{Aurochs (Chen et al., 2018):} \cite{chen2018aurochs} designed a data-driven TE framework for enterprise networks, but relied on slow offline training pipelines without closed-loop real-time failover.
    \item \textbf{RL-Routing (Chen et al., 2020):} \cite{chen2020rlrouting} proposed an SDN routing algorithm based on standard Deep Q-Networks evaluated against OSPF and Least-Loaded Routing on topologies such as NSFNet. While RL-Routing demonstrated the potential of model-free reinforcement learning in OpenFlow environments, it relied on a single-stream Q-network (susceptible to maximization bias), uniform random experience replay (which fails to prioritize critical tail-congestion events), unconstrained next-hop decisions (which can create transient routing loops or dead ends without topological action masking), and an idealized single-controller architecture without high-availability failover.
    \item \textbf{RouteNet and RouteNet-Fermi (Rusek et al., 2020; Almasan et al., 2022):} \cite{rusek2019routenet, almasan2022routenet} leveraged Graph Neural Networks (GNNs) to model the non-linear relationship between topology, traffic matrix, and packet-level delay/jitter distributions. While RouteNet-Fermi achieves structural scale-invariance across arbitrary topologies, it operates primarily as an offline digital-twin forward performance evaluator rather than an autonomous closed-loop routing actuator, relying on external meta-heuristic search to select forwarding paths.
    \item \textbf{Multi-Path DRL Routing (Sun et al., 2021):} \cite{sun2021multi} developed multi-path DRL traffic engineering with dynamic split-ratio tuning over OpenFlow. However, per-packet multi-path splitting introduces significant TCP out-of-order delivery penalties, underscoring the necessity of unsplittable flow allocation for real-time transport streams.
    \item \textbf{Multi-Agent SDN TE (Xu et al., 2022):} \cite{xu2022multiagent} explored multi-agent reinforcement learning for large-scale multi-domain SDN, decomposing wide-area routing into regional sub-controllers. While reducing state dimension per agent, inter-controller communication overhead and non-stationarity during joint exploration remain significant deployment challenges.
\end{itemize}

\section{High Availability and Resilience in SDN Control Planes}
Carrier networks may target $99.999\%$ availability (maximum 5.26 minutes of downtime per year). Distributed controllers such as ONOS and OpenDaylight provide clustering mechanisms. Many DRL-for-routing evaluations nevertheless treat the controller as an idealized single-node abstraction, making controller-crash recovery, socket reconnection, and state synchronization comparatively less explored in the selected routing literature.

\section{Systematic Comparison of Related Work}
Table~\ref{tab:related_work} provides a rigorous, multi-dimensional comparison between existing traffic engineering paradigms and the proposed D3QN platform.

\begin{table}[htbp]
\centering
\caption{Systematic Comparison of Related Work vs. Proposed D3QN Platform}
\label{tab:related_work}
\scriptsize
\begin{tabularx}{\textwidth}{l >{\raggedright\arraybackslash}p{2.2cm} >{\centering\arraybackslash}p{1.6cm} >{\raggedright\arraybackslash}X c >{\centering\arraybackslash}p{2.2cm} c}
\toprule
\textbf{Framework} & \textbf{Core Algorithm} & \textbf{Telemetry} & \textbf{Reward Formulation} & \textbf{Replay} & \textbf{HA Cluster} & \textbf{Zero-Shot} \\
\midrule
OSPF (RFC 2328) \cite{moy1998ospf} & Dijkstra SPF & Static & None (Admin) & None & None & N/A \\
ECMP \cite{moy1998ospf} & Hash Multipath & Static & None (Equal Cost) & None & None & N/A \\
Fortz \& Thorup \cite{fortz2000internet} & Local Search Heuristic & Periodic & Convex Congestion & None & None & No \\
Hedera \cite{al2010hedera} & Greedy Flow-Fit & 5-sec deltas & Bisection Bandwidth & None & None & No \\
Google B4 \cite{jain2013b4} & Centralized LP & OpenFlow TM & Priority Max-Min & None & Master-Slave & No \\
Stampa et al. \cite{stampa2017deep} & Flat Standard DQN & 1D Delay & Delay Reduction Only & Uniform & None & No \\
RL-Routing \cite{chen2020rlrouting} & Vanilla DQN & Multi-Hop & Hop / Delay & Uniform & None & No \\
RouteNet \cite{rusek2019routenet} & Graph Neural Net & Full Matrix & Supervised Delay & N/A & None & Yes \\
\textbf{Proposed (Ours)} & \textbf{D3QN + Yen's KSP} & \textbf{10D Norm} & \textbf{Delay, Jitter, Loss, $\Phi(u)$} & \textbf{SumTree} & \textbf{3-Node Pool (Fail-Secure)} & \textbf{Yes} \\
\bottomrule
\end{tabularx}
\end{table}

\section{Research Gap and Key Innovations}
The critical review of existing literature reveals four major research gaps:
\begin{enumerate}
    \item \textbf{Gap 1: Q-Value Overestimation and Action Explosion:} Existing DRL routing approaches use flat DQN architectures that suffer from catastrophic overestimation bias, or unconstrained action spaces that scale exponentially ($O(|V|^2)$), preventing real-time convergence.
    \item \textbf{Gap 2: Loss of Critical Congestion Transitions in Replay:} Standard uniform replay buffers discard or severely dilute rare buffer overflow and link saturation events, causing agents to unlearn defensive rerouting policies.
    \item \textbf{Gap 3: Complete Neglect of Controller High Availability:} Prior DRL-TE publications assume an infallible centralized controller, omitting failover latency, leader election, and state synchronization.
    \item \textbf{Gap 4: Lack of Statistical and Zero-Shot Transfer Rigor:} Most studies evaluate on a single topology under static Poisson traffic, omitting multi-seed ANOVA decomposition and zero-shot transfer evaluations on unvisited graph topologies.
\end{enumerate}

The platform developed in this project directly addresses and resolves all four research gaps.
'''
