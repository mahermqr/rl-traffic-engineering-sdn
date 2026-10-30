# Chapter 2: Background

CHAPTER_2_BACKGROUND = r'''% ============================================================================
% CHAPTER 2: BACKGROUND
% ============================================================================
\chapter{Background}
\label{chap:background}

\section{Hardware, Software Tools, and Key Equipment: Why Each Was Chosen}
In accordance with the Faculty of Engineering graduation project guidelines, this section presents the core equipment, software tools, and frameworks chosen to realize this project, providing a rigorous technical justification for why each tool was selected:

\begin{enumerate}
    \item \textbf{Software-Defined Networking (SDN) and OpenFlow 1.3 Protocol:}
    Traditional distributed routing architectures couple the control logic and packet forwarding hardware within individual closed vendor routers. This architectural coupling prevents global optimization and dynamic policy reconfiguration. SDN was chosen because it cleanly decouples the control plane from the data plane, providing logically centralized network visibility and dynamic software programmability. OpenFlow version 1.3 (ONF TS-006) \cite{onf2012openflow} was specifically selected because:
    \begin{itemize}
        \item It supports multi-stage pipelined Flow Tables and Group Tables.
        \item It provides standardized, high-precision per-port and per-flow byte/packet counters via \code{OFPPortStatsRequest} and \code{OFPFlowStatsRequest}.
        \item It is natively supported by modern kernel-space virtual switches (Open vSwitch) and hardware merchant silicon ASICs.
    \end{itemize}

    \item \textbf{Ryu SDN Controller Framework:}
    The control plane requires an extensible, robust, and event-driven software framework. While monolithic Java-based controllers (such as ONOS or OpenDaylight) provide carrier features, they impose massive memory footprints ($>4$~GB RAM) and high JVM warmup latency. Ryu was selected because:
    \begin{itemize}
        \item It is fully implemented in Python, allowing direct, zero-overhead in-memory integration with scientific computing and machine learning libraries (PyTorch, NumPy, NetworkX).
        \item It utilizes an asynchronous event-driven architecture based on Eventlet green threads, ensuring responsive coroutine handling of OpenFlow messages.
        \item It provides native, robust packet-parsing libraries for LLDP, IPv4, TCP, UDP, and ARP protocols.
    \end{itemize}

    \item \textbf{Mininet Network Emulation Platform:}
    To evaluate the platform under realistic conditions without requiring million-dollar physical switch hardware, an emulation environment is required. Mininet (version 2.3.0) was chosen because:
    \begin{itemize}
        \item Unlike discrete-event software simulators (e.g., NS-3 or OMNeT++), Mininet runs \textbf{real production software}: real Linux kernel network stacks, real Open vSwitch (OVS) kernel datapath modules, and real application binaries (iperf, ping, curl).
        \item It employs lightweight OS-level Linux network namespaces (\code{netns}) and virtual Ethernet (\code{veth}) pairs, enabling high-fidelity emulation of complex 20-switch, 32-host topologies on commodity x86 hardware.
        \item It supports exact, reproducible topological creation via programmatic Python scripts.
    \end{itemize}

    \item \textbf{PyTorch Deep Learning Library:}
    The reinforcement learning intelligence engine requires a high-performance deep learning framework. PyTorch 2.0+ was selected because:
    \begin{itemize}
        \item It provides dynamic computational graphs (eager execution), facilitating rapid forward-inference and transparent backpropagation.
        \item It features highly optimized C++/CUDA tensor kernels with sub-millisecond execution overhead ($0.24$~ms inference for the D3QN agent).
        \item It supports modular neural layers, custom activation functions (LeakyReLU), Layer Normalization, and advanced optimizers (Adam with gradient clipping).
    \end{itemize}

    \item \textbf{Health-Checked Active/Standby High-Availability Architecture:}
    A single centralized SDN controller represents a vulnerable single point of failure (SPOF). To provide fault tolerance and continuous control plane operation, a health-checked active/standby multi-controller pool was implemented. The pool architecture utilizes HTTP health probes to monitor node vitality, initiates sub-millisecond local failover bookkeeping ($0.001$~ms) to designate an available standby, and provides transparent client retry with automated endpoint redirection, avoiding the operational complexity of external consensus daemons while ensuring rapid controller recovery.

    \item \textbf{Programmable Data Planes (P4) and In-Band Network Telemetry (INT):}
    While OpenFlow 1.3 provides standard southbound abstractions, emerging carrier networks are transitioning toward fully programmable data planes. P4 was evaluated as the architectural target for hardware deployment, offering line-rate packet parsing, stateful on-switch register processing, and nanosecond-resolution telemetry without control-plane polling overhead.
\end{enumerate}

\section{Programmable Data Planes (P4) and In-Band Network Telemetry (INT)}
\label{sec:p4_int_background}
To understand the architectural evolution of software-defined forwarding, it is essential to contextualize OpenFlow against modern **Programmable Data Planes** driven by the **P4 (Programming Protocol-Independent Packet Processors)** language:

\begin{enumerate}
    \item \textbf{Limitations of OpenFlow's Fixed Pipeline:}
    OpenFlow 1.3 relies on a standardized, fixed-function packet parser that recognizes a hardcoded set of packet headers (Ethernet, VLAN, IPv4, IPv6, TCP, UDP, MPLS). If a telecommunication carrier introduces a novel encapsulation protocol (e.g., Segment Routing over IPv6, SRv6) or custom telemetry tags, the OpenFlow switch firmware must be completely redesigned. Furthermore, OpenFlow telemetry is fundamentally reactive and asynchronous: port and flow statistics are retrieved via periodic pull requests (\code{OFPPortStatsRequest}), introducing a minimum polling lag of $\Delta t \approx 1.0$~second.

    \item \textbf{The PISA Architecture and P4 Model:}
    The Protocol-Independent Switch Architecture (\textbf{PISA}) introduces a fully programmable packet processing pipeline comprising:
    \begin{itemize}
        \item \textbf{Programmable Parser:} Expressed as a state machine that parses arbitrary, custom-defined header sequences from bitstreams.
        \item \textbf{Ingress Match-Action Stages:} Reconfigurable lookup tables supported by Ternary Content-Addressable Memory (TCAM) and Static RAM (SRAM), accompanied by stateful Register arrays that maintain line-rate state across consecutive packets.
        \item \textbf{Queuing and Traffic Manager:} Manages packet buffer queues, packet replication (multicast), and traffic shaping.
        \item \textbf{Egress Match-Action Stages:} Applies egress modifications, encapsulations, and queuing telemetry insertions.
        \item \textbf{Programmable Deparser:} Reassembles modified headers into outgoing Ethernet bitstreams.
    \end{itemize}

    \item \textbf{In-Band Network Telemetry (INT):}
    Developed by the P4.org telemetry working group, In-Band Network Telemetry (\textbf{INT}) eliminates periodic polling overhead entirely. Instead of an external controller querying switches, transit switches embed real-time metadata directly into the payload or shim encapsulation of user data packets at hardware line rate (e.g., 400 Gbps per port on Intel Barefoot Tofino ASICs). As a packet traverses the network:
    \begin{itemize}
        \item Ingress switches insert an INT header.
        \item Each intermediate hop pushes its unique \textbf{Switch ID}, \textbf{Egress Port}, \textbf{Hop Latency} (measured in nanoseconds), \textbf{Instantaneous Queue Depth}, and \textbf{Congestion Mark}.
        \item Egress sink switches strip the INT telemetry headers and forward raw telemetry digests directly to the DRL inference engine via high-speed UDP streams or Kafka event buses.
    \end{itemize}

    \item \textbf{Design Justification for the Current Prototype:}
    Although P4/INT represents the definitive future for hardware merchant silicon, this project deliberately deploys OpenFlow 1.3 on Open vSwitch (OVS) and Mininet for the primary software prototype. OpenFlow 1.3 is universally supported across commodity Linux network namespaces without requiring specialized P4 compiler toolchains (p4c) or proprietary FPGA/ASIC hardware emulators. Crucially, the 10-dimensional state vector $\mathbf{s} \in \mathbb{R}^{10}$ designed in this project is explicitly architected to map directly onto INT header fields, ensuring seamless future migration to P4-native hardware testbeds.
\end{enumerate}

\section{Mathematical Foundations of Traffic Engineering and UMCF}
A communication network is formally modeled as a directed multigraph $G = (V, E)$, where $V$ represents the set of network nodes (OpenFlow switches) with $|V| = N$, and $E$ represents the set of directed transmission links with $|E| = M$. Each directed edge $e = (u, v) \in E$ is characterized by:
\begin{itemize}
    \item Transmission capacity $C_e > 0$ expressed in Megabits per second (Mbps).
    \item Physical propagation delay $d_{\text{prop}}(e) > 0$ expressed in milliseconds (ms).
    \item Finite buffer queue capacity $B_e$ expressed in packets.
\end{itemize}

Let $\mathcal{K} = \{1, 2, \dots, K\}$ denote the set of active traffic demands (commodities) traversing the network. Each commodity $k \in \mathcal{K}$ is defined by a tuple:
\begin{equation}
k = \left( s_k, t_k, D_k \right)
\end{equation}
where $s_k \in V$ is the ingress source node, $t_k \in V$ is the egress destination node, and $D_k \ge 0$ is the traffic bandwidth demand (in Mbps).

Let $\mathcal{P}_k$ denote the set of loopless directed paths connecting source $s_k$ to destination $t_k$ in $G$. In modern packet networks, per-packet multi-path routing across paths with asymmetric latencies causes severe TCP packet reordering, duplicate ACKs, and catastrophic throughput collapse. Consequently, this work operates strictly within the \textbf{Unsplittable Multi-Commodity Flow (UMCF)} regime. For each demand $k$, we define a binary routing decision variable:
\begin{equation}
x_{k, p} \in \{0, 1\} \quad \forall p \in \mathcal{P}_k
\end{equation}
such that exactly one candidate path is assigned to each demand:
\begin{equation}
\label{eq:path_assignment}
\sum_{p \in \mathcal{P}_k} x_{k, p} = 1 \quad \forall k \in \mathcal{K}
\end{equation}

The aggregate traffic load $\lambda_e$ traversing link $e \in E$ is the sum of bandwidth demands of all commodities routed through link $e$:
\begin{equation}
\lambda_e = \sum_{k \in \mathcal{K}} \sum_{p \in \mathcal{P}_k : e \in p} D_k \cdot x_{k, p} \quad [\text{Mbps}]
\end{equation}
The instantaneous utilization $u_e$ of link $e$ is defined as the ratio of traffic load to physical capacity:
\begin{equation}
u_e = \frac{\lambda_e}{C_e}
\end{equation}

To prevent packet loss, physical link capacity constraints enforce:
\begin{equation}
\label{eq:capacity_constraint}
u_e \le 1.0 \quad \forall e \in E \iff \lambda_e \le C_e
\end{equation}

The general Traffic Engineering objective is to find a binary path assignment matrix $\mathbf{X} = \{x_{k, p}\}$ that minimizes a composite network cost function $\Psi(\mathbf{X})$ while satisfying (\ref{eq:path_assignment}) and (\ref{eq:capacity_constraint}):
\begin{equation}
\min_{\mathbf{X}} \quad \Psi(\mathbf{X}) = \sum_{e \in E} \Phi(u_e) + \alpha \sum_{k \in \mathcal{K}} \text{Delay}(k, \mathbf{X}) + \beta \sum_{k \in \mathcal{K}} \text{Jitter}(k, \mathbf{X})
\end{equation}
where $\Phi(u_e)$ is a convex link congestion penalty function.

\begin{theorem}[NP-Hardness of UMCF]
The Unsplittable Multi-Commodity Flow problem with binary decision variables $x_{k, p} \in \{0, 1\}$ is strongly NP-hard \cite{garey1979computers}.
\end{theorem}
\begin{proof}
The proof proceeds by reduction from the classical \textsc{Partition} problem. Given a set of integers $\mathcal{S} = \{w_1, w_2, \dots, w_n\}$ summing to $2W$, the partition problem asks whether there exists a subset $\mathcal{S}' \subset \mathcal{S}$ such that $\sum_{i \in \mathcal{S}'} w_i = W$. We construct a 2-node graph $G=(V, E)$ with source $s$ and destination $t$ connected by two parallel directed links $e_1, e_2$, each with capacity $C_{e_1} = C_{e_2} = W$. For each integer $w_i$, define a commodity $k_i = (s, t, w_i)$. Any valid unsplittable routing assignment satisfying $u_{e_1} \le 1.0$ and $u_{e_2} \le 1.0$ corresponds directly to a valid partition of $\mathcal{S}$. Because \textsc{Partition} is NP-complete, finding an optimal unsplittable flow assignment is strongly NP-hard.
\end{proof}

\section{Queueing Delay, Bufferbloat, and RFC 3393 Jitter Modeling}
To evaluate link latency realistically without arbitrary heuristics, we model switch egress port buffers using stochastic queueing theory. Assuming Poisson packet arrivals with aggregate rate $\lambda_e$ and exponentially distributed packet transmission service times with service rate $\mu_e = C_e / \bar{L}$ (where $\bar{L}$ is the mean packet size), each switch port buffer behaves as an $M/M/1/K$ queue with finite buffer capacity $K_B$:

\begin{enumerate}
    \item \textbf{Kleinrock Mean Queueing Delay:}
    Under stable traffic regimes ($\rho_e = \lambda_e / \mu_e < 1.0$), the mean queueing delay $W_{q}(e)$ experienced by packets in the buffer is derived via Kleinrock's formula \cite{kleinrock1964communication}:
    \begin{equation}
    W_{q}(e) = \frac{\rho_e}{\mu_e(1 - \rho_e)} = \frac{\lambda_e}{\mu_e(\mu_e - \lambda_e)} \quad [\text{seconds}]
    \end{equation}
    The total end-to-end latency $D(p)$ along path $p$ is the sum of physical propagation delays and queueing delays across all constituent hops:
    \begin{equation}
    D(p) = \sum_{e \in p} \left( d_{\text{prop}}(e) + W_{q}(e) \right) \quad [\text{ms}]
    \end{equation}

    \item \textbf{Finite Buffer Packet Drop Probability:}
    When traffic approaches or exceeds capacity, the finite switch buffer overflows. The stationary probability $P_{\text{loss}}(e)$ of a packet arriving to find a full buffer (inducing tail-drop) in an $M/M/1/K_B$ queue is given by:
    \begin{equation}
    P_{\text{loss}}(e) = \frac{(1 - \rho_e)\rho_e^{K_B}}{1 - \rho_e^{K_B + 1}}
    \end{equation}
    For a path $p$, the overall packet delivery success rate is $\prod_{e \in p} (1 - P_{\text{loss}}(e))$, yielding path drop probability:
    \begin{equation}
    P_{\text{loss}}(p) = 1 - \prod_{e \in p} \left(1 - P_{\text{loss}}(e)\right)
    \end{equation}

    \item \textbf{Packet Delay Variation (Jitter, RFC 3393):}
    The Internet Engineering Task Force (IETF) RFC 3393 specifies the IP Packet Delay Variation (IPDV) metric \cite{deroo2002ip}. For a sequence of consecutive packets $\{1, 2, \dots, M\}$ traversing path $p$ with measured one-way delays $\{D_1, D_2, \dots, D_M\}$, the sample variance jitter $J(p)$ is formalized as:
    \begin{equation}
    J(p) = \sqrt{\frac{1}{M - 1} \sum_{i=1}^M \left( D_i - \bar{D} \right)^2} \quad [\text{ms}]
    \end{equation}
\end{enumerate}

\section{Deep Reinforcement Learning Foundations}
Reinforcement learning addresses the problem of an autonomous agent learning optimal control policies through trial-and-error interactions with a dynamic environment. The underlying decision process is formulated as an infinite-horizon discounted Markov Decision Process (\textbf{MDP}), defined by the 5-tuple:
\begin{equation}
\mathcal{M} = \left( \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \gamma \right)
\end{equation}
where $\mathcal{S}$ is the state space, $\mathcal{A}$ is the discrete action space, $\mathcal{P}(s' | s, a) = \mathbb{P}(S_{t+1} = s' | S_t = s, A_t = a)$ represents transition probability dynamics, $\mathcal{R}(s, a)$ is the scalar reward function, and $\gamma \in [0, 1)$ is the temporal discount factor.

The agent's goal is to learn a policy $\pi(a | s)$ that maximizes the expected cumulative discounted return $G_t$:
\begin{equation}
G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1}
\end{equation}
Under policy $\pi$, the state-action value function $Q^\pi(s, a)$ satisfies the fundamental Bellman equation \cite{sutton2018reinforcement}:
\begin{equation}
Q^\pi(s, a) = \mathbb{E}\left[ R_{t+1} + \gamma \sum_{a' \in \mathcal{A}} \pi(a' | S_{t+1}) Q^\pi(S_{t+1}, a') \;\middle|\; S_t = s, A_t = a \right]
\end{equation}
The optimal action-value function $Q^*(s, a) = \max_\pi Q^\pi(s, a)$ satisfies the non-linear Bellman optimality equation:
\begin{equation}
Q^*(s, a) = \mathbb{E}\left[ R_{t+1} + \gamma \max_{a' \in \mathcal{A}} Q^*(S_{t+1}, a') \;\middle|\; S_t = s, A_t = a \right]
\end{equation}

\section{Dueling Double Deep Q-Networks (D3QN)}
In high-dimensional state spaces, tabular Q-learning fails due to the curse of dimensionality. Deep Q-Networks (DQN) \cite{mnih2015human} approximate $Q^*(s, a)$ using a deep neural network parameterized by weights $\theta$. However, standard DQN suffers from two critical flaws in network routing:
\begin{enumerate}
    \item \textbf{Severe Q-Value Overestimation Bias:} The maximization operator $\max_{a'} Q(s', a'; \theta)$ systematically overestimates action values in noisy networking environments.
    \item \textbf{Representational Inefficiency:} In many routing states, the underlying state value $V(s)$ (overall network health) is critical, regardless of which candidate path is chosen.
\end{enumerate}

To overcome these deficiencies, this work implements a \textbf{Dueling Double Deep Q-Network (D3QN)} combining two architectural breakthroughs:

\begin{enumerate}
    \item \textbf{Double Q-Learning Target Decoupling:}
    Van Hasselt et al. \cite{vanhasselt2016deep} showed that decoupling action selection from action evaluation can reduce maximization bias. Action selection is governed by the online network parameters $\theta$, while target evaluation is governed by a delayed target network $\theta^-$:
    \begin{equation}
    \label{eq:double_q_target}
    Y_t^{\text{DDQN}} = R_{t+1} + \gamma Q\left(S_{t+1}, \arg\max_{a' \in \mathcal{A}} Q(S_{t+1}, a'; \theta); \theta^-\right)
    \end{equation}
    The target network parameters $\theta^-$ are smoothly tracked via Polyak soft updates with coefficient $\tau = 0.005$:
    \begin{equation}
    \theta^- \leftarrow \tau \theta + (1 - \tau)\theta^-
    \end{equation}

    \item \textbf{Dueling Neural Network Stream Factorization:}
    Wang et al. \cite{wang2016dueling} introduced the Dueling architecture, which factorizes the representation into two separate streams following shared feature extraction:
    \begin{itemize}
        \item A scalar State-Value stream $V(s; \theta, \beta) \in \mathbb{R}$.
        \item A vector Action-Advantage stream $A(s, a; \theta, \alpha) \in \mathbb{R}^{|\mathcal{A}|}$.
    \end{itemize}
    To guarantee identifiability (preventing arbitrary scalar offsets between $V$ and $A$), the aggregation layer enforces mean-centering:
    \begin{equation}
    \label{eq:dueling_aggregation}
    Q(s, a; \theta, \alpha, \beta) = V(s; \theta, \beta) + \left( A(s, a; \theta, \alpha) - \frac{1}{|\mathcal{A}|} \sum_{a' \in \mathcal{A}} A(s, a'; \theta, \alpha) \right)
    \end{equation}
\end{enumerate}

\section{Prioritized Experience Replay (PER) with Binary SumTree}
Standard DQN samples past transitions uniformly from a memory buffer. However, in network routing, catastrophic congestion events (such as buffer drops and link failures) are rare but critical. Uniform sampling drowns these rare events in seas of normal traffic. 

Prioritized Experience Replay (PER) \cite{schaul2016prioritized} samples transitions with probability proportional to their Temporal Difference (TD) error magnitude $\delta_i$:
\begin{equation}
\delta_i = Y_i^{\text{DDQN}} - Q(s_i, a_i; \theta)
\end{equation}
The priority $p_i$ of transition $i$ is formalized as:
\begin{equation}
p_i = \left( |\delta_i| + \epsilon_{\text{per}} \right)^\alpha
\end{equation}
where $\epsilon_{\text{per}} = 10^{-5}$ guarantees non-zero priority, and $\alpha \in [0, 1]$ controls prioritization aggressiveness ($\alpha = 0$ corresponds to uniform sampling, $\alpha = 0.6$ is optimal). The sampling probability $P(i)$ is:
\begin{equation}
P(i) = \frac{p_i}{\sum_{k=1}^N p_k}
\end{equation}

Non-uniform sampling introduces distribution bias. To ensure unbiased stochastic gradient descent, importance-sampling (IS) weights $w_i$ are computed:
\begin{equation}
w_i = \left( \frac{1}{N \cdot P(i)} \right)^\beta \Big/ \max_{j} w_j
\end{equation}
where $\beta$ is annealed linearly from $\beta_0 = 0.4$ to $1.0$ during training.

To avoid costly $O(N)$ linear scans when sampling and updating priorities over buffers with $N = 50,000$ transitions, we implement a \textbf{Binary SumTree}. A SumTree is a complete binary tree where:
\begin{itemize}
    \item The root node stores the total cumulative priority sum $p_{\text{total}} = \sum_{k=1}^N p_k$.
    \item Each parent node equals the exact sum of its two children: $P_{\text{parent}} = P_{\text{left}} + P_{\text{right}}$.
    \item Leaf nodes store the individual transition priorities $p_i$.
\end{itemize}
Both sample retrieval and priority updates execute in strictly $O(\log N)$ time, enabling real-time training steps without control plane stalling.
'''
