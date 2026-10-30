# Chapter 6: Future Work

CHAPTER_6_FUTURE_WORK = r'''% ============================================================================
% CHAPTER 6: FUTURE WORK
% ============================================================================
\chapter{Future Work}
\label{chap:future}

Building upon the successful empirical validation of this graduation project, six concrete research directions are identified to advance the platform toward multi-domain commercial carrier deployment:

\section{P4 Programmable Data Planes and In-Band Network Telemetry}
The current software architecture polls switch port counters every $\Delta t = 1.0$~s via OpenFlow \code{OFPPortStatsRequest}. Future work will transition the data plane from OpenFlow to \textbf{P4 (Programming Protocol-Independent Packet Processors)} running on Intel Barefoot Tofino ASICs. Implementing \textbf{In-Band Network Telemetry (INT)} will enable switches to insert hardware timestamps and queue occupancy directly into packet headers, providing sub-microsecond telemetry without control plane polling overhead.

\section{Multi-Agent RL for Inter-Domain Carrier Transit}
Modern global networks span multiple Autonomous Systems (ASes) managed by independent carriers. Future research will extend the single D3QN agent into a \textbf{Multi-Agent Reinforcement Learning (MARL)} framework, using centralized training with decentralized execution (CTDE) to coordinate inter-domain traffic engineering across peer networks while preserving administrative data privacy.

\section{Graph Neural Networks for Topological Invariance}
While the 10D normalized state representation demonstrated strong zero-shot generalization on small-world graphs, future iterations will integrate \textbf{Graph Neural Networks (GNNs)} (such as Graph Attention Networks, GAT) directly into the DRL encoder. This will enable the policy network to ingest arbitrary topological graphs as native edge-node embeddings, achieving complete topological scale invariance.

\section{Constrained MDPs and Formal Safety Verification}
To completely eliminate exploratory packet drops during online continuous learning, future research will formulate routing as a \textbf{Constrained Markov Decision Process (C-MDP)}. Leveraging Control Barrier Functions (CBFs) and Lyapunov-based safety layers will provide mathematical guarantees that exploratory routing actions never violate physical link capacity constraints.

\section{Optical Transport Network and Reconfigurable Wavelength Routing}
Extending the platform beyond layer-3 packet switching into optical transport networks (OTN) will enable the DRL agent to dynamically adjust Reconfigurable Optical Add-Drop Multiplexers (ROADMs), switching lightpaths and reallocating optical spectrum in response to long-term macro traffic shifts.

\section{Zero-Trust Control-Plane Cryptographic Attestation}
To defend against Byzantine adversaries and compromised switches, future work will integrate zero-trust cryptographic mutual TLS attestation and lightweight consensus verification across all inter-controller heartbeat channels.
'''
