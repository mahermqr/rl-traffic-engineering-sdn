# Chapter 3: Related Work

CHAPTER_3_RELATED = r'''
\chapter{Related Work}
\label{chap:related}

This chapter reviews systems relevant to the project's route selector, controller integration, and evaluation. Recent work is considered first, followed by the earlier routing methods used as references. The purpose is to explain the design choices, rather than to claim that this prototype replaces those systems.

\section{Recent Learning-Based Routing Systems}
\subsection{ENERO}
ENERO combines a graph-based reinforcement-learning policy with a local-search stage to improve WAN routing configurations \cite{almasan2022enero}. Its two-stage design is relevant because it shows that a learned decision can be combined with a conventional optimisation method. The present project instead selects one of four candidate paths using a fixed summary vector. This is simpler to integrate with the controller, but retains less information about the graph.

\subsection{Graph-Based Routing Agents}
Almasan et al. combine graph neural networks with reinforcement learning for an optical-routing use case \cite{almasan2022gnn}. Their work evaluates transfer to unseen topologies. It informs the choice to examine transfer separately in this project, while also identifying a limitation of the ten-feature representation. The current implementation uses path summaries and does not implement a graph neural network; its transfer results therefore apply only to the sampled graphs and workloads.

\subsection{RouteNet-Fermi}
RouteNet-Fermi predicts network delay, jitter, and loss using a graph neural network \cite{almasan2022routenet}. It is a performance model rather than the same route-selection task. Its relevance is the need to represent topology, traffic, and queue behaviour accurately. The present project uses a simpler analytical queue model and checks it against separate packet-emulation observations. Results from the two evaluation methods are reported separately.

\section{Earlier Systems and Routing Baselines}
RL-Routing studies reinforcement-learning routing with throughput and delay rewards and compares it with OSPF and least-loaded routing \cite{chen2020rlrouting}. This supports the inclusion of simple routing baselines in the project. Stampa et al. also investigate learned routing configurations for reducing delay \cite{stampa2017deep}. The local plain-DQN ablation is a project implementation baseline, not a reproduction of either publication.

Earlier SDN systems demonstrate other ways to allocate traffic. Hedera schedules flows in data-centre networks \cite{al2010hedera}, while B4 and SWAN use centralised optimisation for WAN traffic allocation \cite{jain2013b4,hong2013achieving}. They provide context for controller-based traffic management, but differ from the small virtual testbed and per-flow route selector built here.

The project also compares with shortest-path and equal-cost forwarding methods \cite{moy1998ospf}. These baselines are useful because they are inexpensive and provide predictable reference behaviour. Least-loaded routing provides a further check on whether the trained model offers a practical benefit over a load-aware heuristic.

\section{How Related Work Informed the Project}
Table~\ref{tab:related_work} relates the reviewed systems to the final implementation.

\begin{table}[htbp]
\centering
\caption{Related Systems and Their Relevance to the Project}
\label{tab:related_work}
\small
\begin{tabularx}{\textwidth}{p{3.0cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X}
\toprule
System or approach & Relevant feature & Project design decision \\
\midrule
ENERO (2022) & Learned routing combined with local search & Compare the neural policy with a separate heuristic-assisted mode. \\
DRL with GNNs (2022) & Graph-based representation and transfer tests & Keep the present input small and state its transfer limits. \\
RouteNet-Fermi (2023) & Learned prediction of network performance & Distinguish the analytical model from packet measurements. \\
RL-Routing (2020) & Throughput/delay rewards and routing comparisons & Include SPF and least-loaded baselines. \\
Hedera, B4, and SWAN & Controller-based traffic allocation & Use a controller to install routes and collect counters. \\
\bottomrule
\end{tabularx}
\end{table}

To systematically situate this dissertation within the broader traffic-engineering landscape, Table~\ref{tab:taxonomy} presents a comparative taxonomy contrasting the EC499 platform against representative classical SDN systems, centralized optimization frameworks, and deep reinforcement learning routing architectures across six key architectural dimensions: algorithmic methodology, state observation representation, action space structure, control plane substrate, loop/forwarding safety mechanisms, and empirical evaluation fidelity.

\begin{table}[htbp]
\centering
\caption{Comparative Taxonomy Contrasting EC499 with State-of-the-Art SDN TE and DRL Routing Systems.}
\label{tab:taxonomy}
\scriptsize
\setlength{\tabcolsep}{2.5pt}
\begin{tabularx}{\linewidth}{>{\raggedright\arraybackslash}p{1.7cm} >{\raggedright\arraybackslash}p{2.1cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}p{1.6cm} >{\raggedright\arraybackslash}p{1.6cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X}
\toprule
\textbf{System} & \textbf{Algorithm} & \textbf{State Representation} & \textbf{Action Space} & \textbf{Substrate} & \textbf{Safety Mechanism} & \textbf{Evaluation Fidelity} \\
\midrule
Hedera \cite{al2010hedera} & Demand-fit heuristic & Host flow rates & Discrete path set & OpenFlow & Flow pre-reservation & Hardware \& Mininet \\
B4 / SWAN \cite{jain2013b4,hong2013achieving} & Centralized LP / TE & Tunnel traffic matrices & Continuous split ratios & OpenFlow / BGP & Bandwidth reservations & Production WAN hardware \\
Stampa et al. \cite{stampa2017deep} & Single DQN & Traffic matrix vector & Discrete path index & OpenFlow / Ryu & None (unconstrained) & OMNeT++ discrete-event sim \\
RL-Routing \cite{chen2020rlrouting} & Deep DRL (DDPG) & Link utilization vector & Continuous flow fractions & OpenFlow & Boundary clipping & Mininet network emulation \\
ENERO \cite{almasan2022enero} & DRL + Local Search & Graph (Message-Passing GNN) & Discrete link weights & P4 / OpenFlow & Local search validation & OMNeT++ packet simulation \\
RouteNet-Fermi \cite{almasan2022routenet} & Graph Neural Net & Graph topology \& queues & Performance inference & SDN Telemetry & GNN calibration & Hardware testbed \& sim \\
\midrule
\textbf{EC499 (This Work)} & \textbf{Dueling D3QN + SumTree PER} & \textbf{10-D graph-invariant summary vector} & \textbf{Discrete $K=4$ loopless candidate paths} & \textbf{Ryu OpenFlow 1.3 (Flow/Group)} & \textbf{Precomputed simple paths \& shadow reservation} & \textbf{500-step sim + 120-run Mininet emulation} \\
\bottomrule
\end{tabularx}
\end{table}

\section{Chapter Summary}
The reviewed work supports the use of network-state information, reproducible comparisons, and explicit transfer tests. The project brings these ideas together in a smaller software prototype with controller integration, a dashboard, and separate recovery tests. The next chapter describes the implemented modules, the experiment procedures, and the final results.
'''
