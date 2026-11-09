# Chapter 2: Background

CHAPTER_2_BACKGROUND = r'''
\chapter{Background}
\label{chap:background}

This chapter introduces the equipment, software, and routing concepts needed to understand the project. It explains their role in the implementation; detailed program behaviour and test results are presented in Chapter~\ref{chap:project}.

\section{Development and Test Environment}
The project uses a Linux virtual machine for development and network emulation. A virtual machine makes the setup accessible without a physical switch laboratory, although processor scheduling and shared host resources can influence timings. The supplied VMware configuration is shown in Appendix~\ref{app:manual}. Software versions for the packet experiment are taken from its saved environment manifest rather than inferred from the current machine.

\section{Software Tools and Reasons for Selection}
Table~\ref{tab:tools} summarizes the software packages, libraries, and protocols employed across the control, data, and experimental planes, detailing their specific architectural roles and selection rationales.

\begin{table}[htbp]
\centering
\caption{Main Software Tools and Their Roles in the Project}
\label{tab:tools}
\small
\begin{tabularx}{\textwidth}{p{2.8cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X}
\toprule
Tool & Project role & Reason for selection \\
\midrule
Python & Controller logic, experiments, and analysis & Allows the controller and learning components to share data structures. \\
Ryu & OpenFlow controller application & Provides packet parsing, switch events, and access to OpenFlow messages. \\
OpenFlow 1.3 & Communication with switches & Supports forwarding-rule installation and port/flow counter requests \cite{mckeown2008openflow,onf2012openflow}. \\
Open vSwitch & Software forwarding plane & Runs with Mininet and exposes flow tables and port counters. \\
Mininet & Packet-emulation testbed & Runs Linux network stacks and application traffic in network namespaces. \\
PyTorch & Neural-network implementation & Supports training, model saving/loading, and CPU inference. \\
NetworkX & Topology and path processing & Provides graph structures and shortest-path routines. \\
NumPy and Matplotlib & Data analysis and figures & Support numerical summaries and reproducible plots. \\
iperf and ping & Packet-test measurements & Supply transport throughput/UDP statistics and separate ICMP diagnostics. \\
\bottomrule
\end{tabularx}
\end{table}

Two Python environments are used because the legacy Ryu/Eventlet stack and the scientific tools have different compatibility requirements. The packet runner uses the scientific environment with access to the system Mininet bindings; the controller is started using its separate Python 3.10 environment. This separation is important when reproducing the project.

\section{Software-Defined Networking and Routing}
In software-defined networking, the controller computes forwarding decisions and the switches apply installed rules. For this project, the controller obtains topology information through discovery events and derives link rates from differences between successive byte-counter readings. It then chooses an output path and sends OpenFlow rule updates.

The comparison includes an OSPF-style inverse-capacity cost baseline, hop-count shortest-path routing, equal-cost multipath routing, widest-shortest-path routing, and least-loaded routing. These provide useful reference behaviours. The software-model OSPF-style baseline implements route costs rather than the full distributed OSPF protocol \cite{moy1998ospf}. The packet experiment uses the separate hop-count SPF and least-loaded policies.

For a directed link \(e\), utilisation is the offered load divided by capacity:
\begin{equation}
u_e=\frac{\lambda_e}{C_e}.
\end{equation}
Here both \(\lambda_e\) and \(C_e\) are expressed in Mbps. Values above one represent overload in the software model. Each traffic demand is assigned a single candidate path:
\begin{equation}
\label{eq:path_assignment}
\sum_{p\in\mathcal{P}_k}x_{k,p}=1,\qquad x_{k,p}\in\{0,1\}.
\end{equation}
A capacity-feasible assignment would also require
\begin{equation}
\label{eq:capacity_constraint}
\sum_{k}\sum_{p:e\in p}d_kx_{k,p}\le C_e.
\end{equation}
The learned reward encourages lower congestion but does not enforce these inequalities as hard admission constraints. The implemented candidate paths and reward are described in the design section.

\section{Learning-Based Route Selection}
Reinforcement learning formalizes optimal sequential decision-making within the framework of a Markov Decision Process (MDP) defined by the 5-tuple $\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \gamma \rangle$, where $\mathcal{S}$ represents the state space, $\mathcal{A}$ is the action space, $\mathcal{P}(s' \mid s, a) = \mathbb{P}(S_{t+1}=s' \mid S_t=s, A_t=a)$ defines the environmental transition dynamics, $\mathcal{R}(s, a) = \mathbb{E}[R_{t+1} \mid S_t=s, A_t=a]$ is the immediate scalar reward function, and $\gamma \in [0, 1)$ is the temporal discount factor \cite{sutton2018reinforcement}. Under policy $\pi(a \mid s)$, the expected return from state-action pair $(s, a)$ is denoted by the action-value function $Q^\pi(s, a) = \mathbb{E}_\pi \left[ \sum_{k=0}^\infty \gamma^k R_{t+k+1} \;\middle|\; S_t=s, A_t=a \right]$. The optimal policy $\pi^*$ satisfies the fundamental Bellman Optimality Equation:
\begin{equation}
\label{eq:bellman_optimality}
Q^*(s, a) = \mathcal{R}(s, a) + \gamma \sum_{s' \in \mathcal{S}} \mathcal{P}(s' \mid s, a) \max_{a' \in \mathcal{A}} Q^*(s', a').
\end{equation}

In high-dimensional state spaces where tabular dynamic programming is intractable, Deep Q-Networks (DQN) approximate $Q^*(s, a)$ with a parameterized neural network $Q(s, a; \theta)$ \cite{mnih2015human}. The standard single-DQN optimizes the parameter vector $\theta$ by minimizing the mean squared Bellman error against a slowly varying target network parameterized by $\theta^-$:
\begin{equation}
\label{eq:standard_dqn_target}
Y_t^{\text{DQN}} = R_{t+1} + \gamma \max_{a' \in \mathcal{A}} Q(S_{t+1}, a'; \theta^-).
\end{equation}
However, single-DQN incurs an upward maximization bias due to the Jensen-type inequality $\mathbb{E}[\max_a (Q(s, a) + \epsilon_a)] \ge \max_a \mathbb{E}[Q(s, a)]$ when evaluation noise $\epsilon_a$ is present. To prevent systematic overestimation of candidate path values, Double DQN decouples greedy action selection from action evaluation \cite{vanhasselt2016deep}:
\begin{equation}
\label{eq:double_q_target}
Y_t^{\text{DDQN}} = R_{t+1} + \gamma Q\left(S_{t+1}, \arg\max_{a' \in \mathcal{A}} Q(S_{t+1}, a'; \theta); \, \theta^-\right).
\end{equation}
Terminal transitions omit the discounted next-state term. Rather than performing abrupt periodic hard updates, the target parameters $\theta^-$ track the online parameters $\theta$ continuously via a Polyak soft-update rule (Polyak-Rupert tracking) with soft-update parameter $\tau \ll 1$ ($\tau = 0.005$):
\begin{equation}
\label{eq:polyak_target_update}
\theta^- \leftarrow \tau \theta + (1 - \tau) \theta^-.
\end{equation}

The dueling network architecture further improves policy evaluation by factoring the scalar state-action value into separate state-value $V(s)$ and state-dependent action-advantage $A(s, a)$ streams \cite{wang2016dueling}. To guarantee identifiability---ensuring that $V(s)$ accurately reflects the state value without shifting arbitrary constants between streams---the advantage outputs are centralized by subtracting their discrete mean:
\begin{equation}
\label{eq:dueling_aggregation}
Q(s, a; \theta, \alpha, \beta) = V(s; \theta, \beta) + \left( A(s, a; \theta, \alpha) - \frac{1}{|\mathcal{A}|} \sum_{a' \in \mathcal{A}} A(s, a'; \theta, \alpha) \right).
\end{equation}
A complete mathematical proof of this identifiability condition and gradient uniqueness is provided in Appendix~\ref{app:math_proofs}.

\section{Experience Replay and Prioritized Sampling}
Replay stores previous transitions so they can be reused during training, breaking temporal autocorrelation across consecutive state transitions. Uniform experience replay selects transitions uniformly at random ($P(i) = 1/N$), which dilutes rare high-error transitions---such as transient link-saturation and buffer-overflow events---amid abundant nominal samples. Prioritized Experience Replay (PER) addresses this limitation by sampling transitions proportionally to their Temporal Difference (TD) error magnitude \cite{schaul2016prioritized}.

For transition $i = (S_i, A_i, R_i, S'_{i})$, the double-DQN TD error is formulated as:
\begin{equation}
\label{eq:td_error}
\delta_i = R_i + \gamma Q\left(S'_{i}, \arg\max_{a'} Q(S'_{i}, a'; \theta); \, \theta^-\right) - Q(S_i, A_i; \theta).
\end{equation}
The transition priority $p_i$ is computed with a small positive constant $\epsilon_{\text{per}} = 0.01$ to ensure non-zero sampling probability, and an exponent $\alpha \in [0, 1]$ determining the degree of prioritization:
\begin{equation}
\label{eq:per_priority}
p_i = \left( |\delta_i| + \epsilon_{\text{per}} \right)^\alpha.
\end{equation}
When $\alpha = 0$, sampling collapses to the uniform baseline; $\alpha = 0.6$ is deployed in the prototype. The discrete sampling probability distribution across buffer capacity $N$ is defined as:
\begin{equation}
\label{eq:per_probability}
P(i) = \frac{p_i}{\sum_{k=1}^N p_k} = \frac{(|\delta_i| + \epsilon_{\text{per}})^\alpha}{\sum_{k=1}^N (|\delta_k| + \epsilon_{\text{per}})^\alpha}.
\end{equation}
Because prioritized sampling alters the empirical data distribution, it introduces estimation bias. This bias is corrected via Importance Sampling (IS) weights $w_i$, scaled by the buffer capacity $N$ and normalized by the maximum weight in the mini-batch to preserve gradient scale:
\begin{equation}
\label{eq:is_weights}
w_i = \left( \frac{1}{N} \cdot \frac{1}{P(i)} \right)^\beta, \qquad \tilde{w}_i = \frac{w_i}{\max_{j} w_j},
\end{equation}
where $\beta \in [0, 1]$ is annealed linearly from initial value $\beta_0 = 0.4$ toward $1.0$ at the conclusion of training:
\begin{equation}
\label{eq:beta_anneal}
\beta_t = \min\left(1.0, \, \beta_0 + t \cdot \Delta\beta \right).
\end{equation}
The network is trained by minimizing the weighted Smooth L1 (Huber) loss over mini-batch size $B = 32$:
\begin{equation}
\label{eq:weighted_huber_loss}
\mathcal{L}(\theta) = \frac{1}{B} \sum_{i=1}^B \tilde{w}_i \cdot \ell_{\delta_0}(\delta_i), \quad \text{where } \ell_{\delta_0}(\delta_i) = \begin{cases} \frac{1}{2}\delta_i^2 & \text{if } |\delta_i| \le \delta_0, \\[1mm] \delta_0 \left( |\delta_i| - \frac{1}{2}\delta_0 \right) & \text{otherwise}, \end{cases}
\end{equation}
with transition threshold $\delta_0 = 1.0$. The project implements the priority prefix sums using a binary SumTree data structure, enabling $O(\log N)$ priority updates and sampling operations.

\section{Understanding the Evaluation Metrics}
The software model estimates queueing effects with an analytical finite-buffer $M/M/1/K$ queueing model applied across each directed link $e \in E$. Let $\lambda_e$ denote the Poisson arrival rate and $\mu_e$ denote the exponential service capacity, yielding link traffic intensity $\rho = \lambda_e / \mu_e = u_e$. Under finite buffer capacity $K = 100$ packets, the steady-state buffer-overflow loss probability $P_K$ is formulated as:
\begin{equation}
\label{eq:mm1k_loss}
P_K = \begin{cases} \dfrac{(1 - \rho)\rho^K}{1 - \rho^{K+1}} & \text{if } \rho \neq 1, \\[2mm] \dfrac{1}{K+1} & \text{if } \rho = 1. \end{cases}
\end{equation}
The expected number of packets residing in the queueing subsystem $L$ is given by:
\begin{equation}
\label{eq:mm1k_length}
L = \frac{\rho}{1 - \rho} - \frac{(K+1)\rho^{K+1}}{1 - \rho^{K+1}},
\end{equation}
and applying Little's Law with effective arrival rate $\lambda_{\text{eff}} = \lambda_e(1 - P_K)$ yields the mean queue waiting time $W_q$ and total link traversal delay $D(e) = d_{\text{prop}}(e) + W$, where total time in the queueing system is $W = W_q + \frac{1}{\mu_e} = \frac{L}{\lambda_{\text{eff}}}$:
\begin{equation}
\label{eq:mm1k_waiting}
W_q = \frac{L}{\lambda_e(1 - P_K)} - \frac{1}{\mu_e}, \qquad D(e) = d_{\text{prop}}(e) + \frac{L}{\lambda_e(1 - P_K)},
\end{equation}
where $d_{\text{prop}}(e)$ represents physical link propagation latency. Because real packet networks exhibit heavy-tailed burst distributions, these analytical formulas serve as controlled simulation estimates rather than direct ASIC measurements.

The Mininet experiment records a different set of observations. Iperf reports transport throughput and, for UDP, datagram loss and jitter. Ping reports round-trip time and ICMP echo loss. TCP retransmission loss is not recorded. In particular, ICMP echo loss must not be interpreted as TCP packet loss, and RTT must not be labelled one-way delay. RFC 3393 provides background on packet delay variation \cite{rfc3393}; the model's bounded jitter proxy is not a direct implementation of that measured statistic.

\section{Controller Recovery}
The project also includes a pool that probes controller endpoints and retries client requests through an available standby. Its purpose is to examine client HTTP recovery after endpoint failure. Local selection bookkeeping, HTTP recovery, and OpenFlow reconnection are different operations and require different measurements. The pool does not implement a distributed replicated log or establish a production availability target.

\section{Chapter Summary}
The tools provide the components needed for a working software prototype: graph processing, a trained route selector, controller integration, a software forwarding plane, and repeatable tests. The main evaluation requirement is to keep model estimates, packet observations, and controller-recovery timings clearly identified. The next chapter explains how related systems influenced these design choices.
'''
