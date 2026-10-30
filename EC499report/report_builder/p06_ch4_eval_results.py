# Chapter 4: The Proposed System (Part 2 - Testing & Evaluation, Results & Discussion)

CHAPTER_4_EVAL_RESULTS = r'''% ----------------------------------------------------------------------------
% 4.3 TESTING AND EVALUATION
% ----------------------------------------------------------------------------
\section{Testing and Evaluation}
\label{sec:testing}

\subsection{Key Performance Metrics}
Performance is evaluated across six rigorous quantitative metrics:
\begin{enumerate}
    \item \textbf{Peak Bottleneck Link Utilization ($u_{\max}$):} Maximum utilization across all links, $\max_{e} u_e$ (\lowerbetter).
    \item \textbf{End-to-End Latency ($D$):} Mean packet transit delay in milliseconds (\lowerbetter).
    \item \textbf{Packet Delay Variation (Jitter, RFC 3393) ($J$):} Standard deviation of packet delays in milliseconds (\lowerbetter).
    \item \textbf{Packet Drop Rate ($P_{\text{loss}}$):} Percentage of transmitted packets dropped due to buffer overflow (\lowerbetter).
    \item \textbf{Jain's Fairness Index ($\mathcal{J}$):} Quantifies bandwidth allocation fairness across commodities \cite{jain1984quantitative}:
    \begin{equation}
    \mathcal{J} = \frac{\left( \sum_{k=1}^K x_k \right)^2}{K \sum_{k=1}^K x_k^2} \quad (\higherbetter)
    \end{equation}
    \item \textbf{High-Availability Failover Latency ($\tau_{\text{fail}}$):} Milliseconds required to promote a standby controller and resume client HTTP REST service (\lowerbetter).
\end{enumerate}

\subsection{Automated Test Suite and Functional Verification}
To guarantee software reliability, the platform includes a 42-test automated unit, integration, and failover test suite (\code{test_suite.py}). The suite verifies:
\begin{itemize}
    \item Neural model weight lifecycle, Polyak soft updates, and dueling aggregation identifiability.
    \item Binary SumTree priority insertion, proportional sampling, and $O(\log N)$ arithmetic.
    \item Active/standby pool initialization, cascaded local failover bookkeeping, endpoint formatting, and API-level behavior. The suite does not implement or validate Raft consensus, quorum election, or OpenFlow reconnection timing.
    \item REST API mutations, topology discovery, and dynamic link failure rerouting.
\end{itemize}
The checked-in suite contains 42 tests. Runtime is environment-dependent and should be reported from the delivery machine rather than treated as a performance result.

\subsection{Claim-to-Evidence Verification Matrix}
Table~\ref{tab:claim_evidence} correlates each engineering claim with its corresponding source code module and verified empirical evidence.

\begin{table}[htbp]
\centering
\caption{Claim-to-Evidence Functional Verification Matrix}
\label{tab:claim_evidence}
\scriptsize
\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash\bfseries}p{2.6cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}p{4.2cm} >{\raggedright\arraybackslash}p{3.4cm}}
\toprule
\textbf{Engineering Claim} & \textbf{Verified Architectural Mechanism} & \textbf{Source File} & \textbf{Empirical Evidence} \\
\midrule
Bottleneck Load Reduction & D3QN + thresholded quadratic congestion term & \code{controller/routing_module.py} & Table~\ref{tab:tournament_results}: $79.1\%$ reduction on Spine-Leaf ($99.84\% \to 20.89\%$; mean $53.9\%$ relative reduction across 5 fabrics) \\
Packet Loss Suppression & Proactive Bypass Rerouting & \code{controller/routing_module.py} & Final seed-42 model run: $0.45\%$ mean estimated loss vs $4.13\%$ OSPF; four entries round to $0.000\%$ \\
Jitter Suppression & RFC 3393 Penalty in Multi-Objective Reward & \code{agent/dqn_router.py} & Table~\ref{tab:tournament_results}: $0.515$~ms vs $15.50$~ms on Spine-Leaf (mean $71.1\%$ suppression across 5 fabrics: $2.71$~ms vs $9.39$~ms OSPF) \\
$O(\log N)$ Replay Scaling & Complete Binary SumTree Data Structure & \code{agent/prioritized_replay.py} & \code{test_sumtree_arithmetic}: PASS \\
Sub-Millisecond Promotion & Local Active Pointer Reassignment & \code{controller/ha_controller_pool.py} & Measured local bookkeeping: \textbf{0.001 ms} \\
Client HTTP Recovery & Client Retry Loop with Standby Redirection & \code{controller/ha_controller_pool.py} & Measured HTTP recovery: \textbf{37.96 ms} \\
Automated Verification & 42 Comprehensive Unit \& Integration Tests & \code{test_suite.py} & 42/42 Tests PASS (3.23 s execution) \\
\bottomrule
\end{tabularx}
\end{table}

% ----------------------------------------------------------------------------
% 4.4 RESULTS AND DISCUSSION
% ----------------------------------------------------------------------------
\section{Results and Discussion}
\label{sec:results}

\subsection{Comprehensive Multi-Topology Routing Tournament Results}
Table~\ref{tab:tournament_results} presents the quantitative results of the routing tournament across all five benchmark topologies under heavy traffic loads. The \textbf{Offload (\%)} column quantifies the Congestion Offload Efficiency $\eta_{\text{offload}} = \frac{N_{\text{rerouted}}}{N_{\text{total}}} \times 100\%$, measuring the percentage of active flows proactively steered onto edge-disjoint non-shortest candidate paths to bypass congested core links.

\begin{table}[htbp]
\centering
\caption{Comprehensive Quantitative Routing Tournament Results Across All Five Benchmark Topologies (Seed-42 Snapshot; see Section~\ref{sec:multiseed_anova} for 125-Seed ANOVA Decomposition)}
\label{tab:tournament_results}
\scriptsize
\begin{tabularx}{\textwidth}{l l *{6}{>{\centering\arraybackslash}X}}
\toprule
\textbf{Topology} & \textbf{Algorithm} & \textbf{Bottleneck (\%)} & \textbf{Latency (ms)} & \textbf{Jitter (ms)} & \textbf{Loss (\%)} & \textbf{Fairness} & \textbf{Offload (\%)} \\
\midrule
\textbf{Hierarchical Tree} & OSPF (RFC 2328) & 56.67\% & 158.68 & 7.716 & 2.611\% & 0.6980 & 37.3\% \\
(7 Switches) & Dijkstra SPF & 42.11\% & 142.40 & 4.414 & 2.504\% & 0.5463 & 0.0\% \\
& ECMP & 41.30\% & 160.82 & 4.503 & 1.941\% & 0.5584 & 20.7\% \\
& \textbf{D3QN (Ours)} & \textbf{43.73\%} & \textbf{167.64} & \textbf{5.322} & \textbf{2.265\%} & \textbf{0.5785} & \textbf{21.3\%} \\
\midrule
\textbf{Fat-Tree Clos} & OSPF (RFC 2328) & 94.58\% & 190.05 & 13.632 & 11.543\% & 0.8718 & 0.0\% \\
(20 Switches) & Dijkstra SPF & 94.62\% & 190.06 & 13.632 & 11.565\% & 0.8717 & 0.0\% \\
& ECMP & 52.68\% & 51.45 & 7.436 & 0.876\% & 0.6583 & 70.0\% \\
& \textbf{D3QN (Ours)} & \textbf{28.81\%} & \textbf{6.57} & \textbf{1.479} & \textbf{0.000\%} & \textbf{0.6961} & \textbf{84.7\%} \\
\midrule
\textbf{Abilene US WAN} & OSPF (RFC 2328) & 33.35\% & 45.31 & 3.445 & 0.027\% & 0.6613 & 2.0\% \\
(12 Switches) & Dijkstra SPF & 33.11\% & 43.56 & 3.538 & 0.027\% & 0.6646 & 0.0\% \\
& ECMP & 32.71\% & 31.53 & 3.439 & 0.001\% & 0.6683 & 2.0\% \\
& \textbf{D3QN (Ours)} & \textbf{31.99\%} & \textbf{26.10} & \textbf{3.434} & \textbf{0.000\%} & \textbf{0.6799} & \textbf{3.3\%} \\
\midrule
\textbf{NSFNet Mesh} & OSPF (RFC 2328) & 49.54\% & 253.47 & 6.681 & 1.057\% & 0.6247 & 4.7\% \\
(14 Switches) & Dijkstra SPF & 49.64\% & 224.62 & 6.692 & 0.872\% & 0.6308 & 0.0\% \\
& ECMP & 44.43\% & 191.68 & 5.453 & 0.936\% & 0.6101 & 20.0\% \\
& \textbf{D3QN (Ours)} & \textbf{28.60\%} & \textbf{19.72} & \textbf{2.810} & \textbf{0.000\%} & \textbf{0.6567} & \textbf{58.0\%} \\
\midrule
\textbf{Spine-Leaf Fabric} & OSPF (RFC 2328) & 99.84\% & 144.21 & 15.500 & 5.396\% & 0.9828 & 0.0\% \\
(12 Switches) & Dijkstra SPF & 99.87\% & 145.47 & 15.500 & 5.429\% & 0.9828 & 0.0\% \\
& ECMP & 55.60\% & 23.63 & 8.102 & 0.122\% & 0.6846 & 74.7\% \\
& \textbf{D3QN (Ours)} & \textbf{20.89\%} & \textbf{2.49} & \textbf{0.515} & \textbf{0.000\%} & \textbf{0.8750} & \textbf{100.0\%} \\
\bottomrule
\end{tabularx}
\end{table}

Figure~\ref{fig:radar_tournament} provides a normalized visual comparison; Table~\ref{tab:tournament_results} should be used for numerical conclusions.

\begin{figure}[!ht]
\centering
\includegraphics[width=0.68\textwidth]{proposal_tournament_radar.png}
\caption{Multi-Dimensional Routing Tournament Radar Performance Comparison Across Algorithms.}
\label{fig:radar_tournament}
\end{figure}

Key empirical takeaways from the multi-topology tournament include:
\begin{itemize}
    \item \textbf{Bottleneck Load Relief:} In the final seed-42 run (150 flows per topology), D3QN has arithmetic mean bottleneck utilization of \textbf{30.80\%} versus \textbf{66.80\%} for OSPF: a $53.9\%$ relative reduction. Its largest displayed reduction is on Spine-Leaf ($99.84\% \to 20.89\%$).
    \item \textbf{Latency and Jitter:} Arithmetic mean modelled latency changes from $158.34$~ms (OSPF) to $44.50$~ms (D3QN), and mean jitter from $9.39$~ms to $2.71$~ms.
    \item \textbf{Topology Specificity and Negative Boundary Result on Hierarchical Tree:} D3QN is not uniformly superior across all fabrics. On the Hierarchical Tree (7 switches), where all inter-pod traffic must transit a single root core switch, graph bisection bandwidth fundamentally limits rerouting freedom. On this topology, static Dijkstra SPF and ECMP outperform D3QN across all metrics: bottleneck utilization is $42.11\%$ (Dijkstra) vs. $43.73\%$ (D3QN), end-to-end latency is $142.40$~ms (Dijkstra) vs. $167.64$~ms (D3QN, an $17.7\%$ latency penalty), jitter is $4.41$~ms vs. $5.32$~ms, and packet loss is $1.94\%$ (ECMP) / $2.50\%$ (Dijkstra) vs. $2.26\%$ (D3QN). Because no alternate paths circumvent the root choke point, RL exploration and candidate-path detours incur unnecessary queuing and hop penalties compared to deterministic shortest paths. Conversely, on rich multipath fabrics (Fat-Tree Clos and Spine-Leaf), D3QN dramatically outperforms all baselines by spreading load across redundant bisection paths.
    \item \textbf{Estimated Packet Loss:} OSPF has an arithmetic mean estimated loss of $4.13\%$, while D3QN has $0.45\%$ in this run. Four D3QN table entries round to $0.000\%$; these are model outputs, not direct hardware measurements.
    \item \textbf{Jain's Fairness Trade-Off:} D3QN exhibits a lower arithmetic mean Jain's Fairness Index (\textbf{0.6972}) than OSPF (\textbf{0.7677}) in this run. This reveals a fundamental operational trade-off: D3QN aggressively deprioritizes or detours specific high-demand flows to protect bottleneck links from queue saturation, slightly lowering fairness in exchange for substantial reductions in global congestion and packet drop rates.
\end{itemize}

\subsection{Latency, Jitter, and Packet Loss Distributions}
Figure~\ref{fig:routing_cdfs} shows the Cumulative Distribution Functions (CDFs) of end-to-end latency and jitter.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.82\textwidth]{routing_cdfs_latency_jitter.png}
\caption{Cumulative Distribution Functions (CDFs) of End-to-End Latency and Jitter Across Protocols.}
\label{fig:routing_cdfs}
\end{figure}

In the plotted CDF data, the D3QN 99th-percentile latency is below $12.0$~ms while the OSPF curve extends beyond $65.0$~ms. This comparison is specific to the plotted workload and queue model.

\subsection{Empirical Packet-Level Mininet Emulation (120-Trial Factorial Evaluation)}
\label{sec:mininet_eval}
To establish empirical packet-level ground truth beyond numerical queueing models, a comprehensive 120-trial evaluation was executed on physical Linux network namespaces using Mininet and Open vSwitch with OpenFlow 1.3 (\code{EC499tests/reproduce_mininet_packet_experiment.py}). 

The factorial design evaluated:
\begin{itemize}
    \item \textbf{Topologies ($2$):} Fat-Tree Clos (20 switches, rich multipath core) and Hierarchical Tree (7 switches, single root bottleneck).
    \item \textbf{Protocols ($2$):} TCP (cubic congestion control with dynamic window scaling) and UDP (constant bit-rate stress traffic).
    \item \textbf{Routing Policies ($3$):} Proposed D3QN (closed-loop neural control), Least-Loaded Routing (LLR heuristic), and Shortest Path First (OSPF/SPF).
    \item \textbf{Replicates ($10$):} 10 fully independent runs per condition with randomized execution order ($2 \times 2 \times 3 \times 10 = 120$ trials, $100\%$ completion rate, seed 2026).
\end{itemize}

Every trial recorded live kernel-level metrics via \code{iperf} throughput probes, ICMP round-trip times (\code{ping} RTT), Open vSwitch port statistics, controller decision overhead, and packet loss. Table~\ref{tab:mininet_measured_summary} presents the empirical condition-level means alongside non-parametric $10,000$-iteration bootstrap $95\%$ confidence intervals computed by \code{analyze_mininet_measured_trials.py}. Note that for Hierarchical Tree UDP under static SPF, deterministic constant-bit-rate generation over an invariant single shortest path produced zero sample variance ($s = 0.00$), causing the bootstrap percentile interval to collapse to $[29.18, 29.18]$.

\begin{table}[htbp]
\centering
\caption{Empirical Packet-Level Mininet Emulation Across 120 Independent Trials (Mean and 95\% Bootstrap Confidence Intervals)}
\label{tab:mininet_measured_summary}
\scriptsize
\begin{tabularx}{\textwidth}{l c c *{4}{>{\centering\arraybackslash}X}}
\toprule
\textbf{Topology} & \textbf{Proto} & \textbf{Policy} & \textbf{Throughput (Mbps)} & \textbf{RTT (ms)} & \textbf{Packet Loss (\%)} & \textbf{Decision Latency (ms)} \\
\midrule
\textbf{Fat-Tree Clos} & TCP & D3QN & \textbf{47.91} $[47.53, 48.24]$ & 20.72 $[20.62, 20.81]$ & 36.0\% $[22.0, 48.0]$ & 0.758 $[0.655, 0.908]$ \\
(Multipath) & & LLR & 47.83 $[47.52, 48.11]$ & 20.59 $[20.53, 20.65]$ & 47.0\% $[35.0, 59.0]$ & 0.016 $[0.015, 0.018]$ \\
& & SPF & 47.64 $[47.38, 47.86]$ & 20.76 $[20.67, 20.83]$ & \textbf{18.0\%} $[8.0, 29.0]$ & 0.028 $[0.025, 0.031]$ \\
\cmidrule(lr){2-7}
& UDP & D3QN & 48.69 $[48.40, 48.97]$ & \textbf{20.55} $[20.48, 20.62]$ & \textbf{14.0\%} $[7.0, 21.0]$ & 0.661 $[0.575, 0.771]$ \\
& & LLR & \textbf{48.87} $[48.74, 49.00]$ & 20.74 $[20.68, 20.79]$ & 17.0\% $[10.0, 24.0]$ & 0.015 $[0.014, 0.016]$ \\
& & SPF & 48.39 $[48.06, 48.67]$ & 20.75 $[20.69, 20.81]$ & 25.0\% $[16.0, 34.0]$ & 0.027 $[0.025, 0.030]$ \\
\midrule
\textbf{Hierarchical Tree} & TCP & D3QN & 34.08 $[33.56, 34.61]$ & 32.41 $[32.06, 32.74]$ & 10.0\% $[2.0, 19.0]$ & 0.554 $[0.490, 0.623]$ \\
(Single Bottleneck) & & LLR & \textbf{38.09} $[35.13, 40.85]$ & \textbf{32.21} $[31.57, 32.73]$ & \textbf{0.0\%} $[0.0, 0.0]$ & 0.013 $[0.012, 0.014]$ \\
& & SPF & 28.56 $[28.32, 28.84]$ & 32.62 $[32.12, 33.09]$ & 10.0\% $[3.0, 18.0]$ & 0.021 $[0.019, 0.023]$ \\
\cmidrule(lr){2-7}
& UDP & D3QN & 29.31 $[29.28, 29.34]$ & \textbf{32.30} $[32.02, 32.55]$ & 10.0\% $[3.0, 17.0]$ & 0.523 $[0.461, 0.597]$ \\
& & LLR & \textbf{31.13} $[29.18, 35.02]$ & 35.25 $[30.95, 40.96]$ & 3.0\% $[0.0, 9.0]$ & 0.013 $[0.012, 0.014]$ \\
& & SPF & 29.18 $[29.18, 29.18]$ & 32.84 $[32.50, 33.29]$ & \textbf{2.0\%} $[0.0, 6.0]$ & 0.021 $[0.019, 0.023]$ \\
\bottomrule
\end{tabularx}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.88\textwidth]{mininet_measured_trials.png}
\caption{Empirical Mininet Packet-Level Measured Performance Distributions (120 Trials: Throughput, RTT Latency, Packet Loss, and Controller Decision Latency).}
\label{fig:mininet_measured_trials}
\end{figure}

Key empirical findings from the 120-trial Mininet emulation include:
\begin{enumerate}
    \item \textbf{Loss Suppression Under UDP Saturation and Heuristic Parity:} On the Fat-Tree Clos fabric under UDP stress, D3QN achieves an empirical packet loss of \textbf{14.0\%} (95\% CI $[7.0, 21.0]$), delivering a notable loss reduction compared to static SPF (\textbf{25.0\%}, 95\% CI $[16.0, 34.0]$). However, D3QN's confidence interval overlaps that of Least-Loaded Routing (\textbf{17.0\%}, 95\% CI $[10.0, 24.0]$), confirming that while both dynamic routing schemes effectively offload congested core links, there is no statistically significant loss divergence between D3QN and the lightweight LLR heuristic under this workload.
    \item \textbf{Heuristic Superiority on Single-Bottleneck Trees:} In the Hierarchical Tree under TCP traffic, D3QN achieves \textbf{34.08 Mbps} (95\% CI $[33.56, 34.61]$), outperforming static SPF (\textbf{28.56 Mbps}, a $+19.3\%$ gain). However, D3QN is outperformed by LLR, which delivers \textbf{38.09 Mbps} (95\% CI $[35.13, 40.85]$) with \textbf{0.0\% packet loss} versus D3QN's \textbf{10.0\% loss}. In single-bottleneck tree topologies where detour diversity is physically absent, greedy dynamic heuristics like LLR distribute queue occupancy more cleanly than deep RL without incurring exploration-induced flow displacement penalties.
    \item \textbf{Transport Protocol Dynamics and TCP Route-Flapping Costs:} Under TCP traffic on the Fat-Tree Clos, D3QN sustains high throughput ($47.91$~Mbps, 95\% CI $[47.53, 48.24]$), but incurs an empirical packet loss of \textbf{36.0\%} (95\% CI $[22.0, 48.0]$), which is higher than static SPF (\textbf{18.0\%}, 95\% CI $[8.0, 29.0]$) and lower than LLR ($47.0\%$). This illustrates a recognized transport-layer challenge: dynamic multi-path rerouting can trigger packet reordering, causing TCP Cubic to interpret out-of-order deliveries as congestion signals, throttling window growth and provoking retransmissions.
    \item \textbf{Controller Overhead Profiling:} Across all 120 trials, D3QN neural inference latency averaged \textbf{0.52--0.76 ms} per flow-setup decision. While higher than static hash lookups ($0.013$--$0.028$~ms), the sub-millisecond decision speed satisfies carrier-grade real-time flow setup requirements while enabling intelligent closed-loop adaptation.
\end{enumerate}

\subsection{Traffic Load Scaling and Congestion Transition}
Figure~\ref{fig:traffic_load_scaling} illustrates network performance across scaled traffic injection rates ($10$~Mbps to $100$~Mbps).

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{traffic_load_scaling_curves.png}
\caption{Traffic Load Scaling Curves Demonstrating Asymptotic Congestion Suppression.}
\label{fig:traffic_load_scaling}
\end{figure}

In the plotted model, static protocols show a sharp latency increase above approximately $70$~Mbps as queues fill. The thresholded congestion term (\ref{eq:barrier_function}) and path selection reduce this increase in the tested scenario; the plot does not establish a universal flat-latency guarantee.

\subsection{Multi-Seed Statistical ANOVA and Variance Decomposition}
To rigorously determine whether performance variations stem from network topology geometry, workload traffic matrices, or model initialization seed artifacts, a balanced factorial experimental design was evaluated across 125 independent runs:
\begin{equation}
N_{\text{eval}} = 5 \text{ Model Seeds } \{101, \dots, 105\} \times 5 \text{ Workload Seeds } \{42, \dots, 46\} \times 5 \text{ Topologies} = 125
\end{equation}
Figure~\ref{fig:training_convergence} shows training convergence trajectories across seeds, and Figure~\ref{fig:multiseed_effects} illustrates paired performance distributions and bootstrap confidence intervals.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{dqn_te_training_convergence.png}
\caption{D3QN Training Convergence Curves Showing Mean Episode Reward and TD Error Loss.}
\label{fig:training_convergence}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{multiseed_paired_effects.png}
\caption{Multi-Seed Paired Performance Effects and Statistical Confidence Intervals.}
\label{fig:multiseed_effects}
\end{figure}

\paragraph{Two-Way ANOVA and Hierarchical Variance Decomposition:}
\label{sec:multiseed_anova}
A two-way factorial Analysis of Variance (ANOVA) and hierarchical variance decomposition (\code{experiment_phase1_suite.py}) isolates the exact percentage of variance attributable to each factor across all measured metrics:
\begin{itemize}
    \item \textbf{Bottleneck Utilization Variance:} Network topology geometry accounts for \textbf{93.51\%} of total variance. In contrast, model initialization seed accounts for only \textbf{0.73\%} of total variance ($F(4, 112) = 0.41, p = 0.80, \eta_p^2 = 0.007$), and workload seed accounts for \textbf{0.02\%}, with residual error at \textbf{5.74\%}. Statistically, this result represents a failure to reject the null hypothesis of equal means across initialization seeds ($p = 0.80$). Because the benchmark topologies differ fundamentally in graph diameter, nodal degree, and bisection bandwidth, topology geometry naturally accounts for $93.51\%$--$98.53\%$ of total variance, while model seed variance remains negligible ($<1\%$).
    \item \textbf{Latency Variance:} Topology geometry explains \textbf{96.76\%} of latency variance, while model seed accounts for \textbf{0.86\%} and workload seed for \textbf{0.03\%}.
    \item \textbf{Packet Loss Variance:} Topology accounts for \textbf{98.53\%} of packet loss variance, with model seed explaining only \textbf{0.66\%}.
\end{itemize}

\paragraph{Paired Difference Bootstrap Analysis with 95\% Confidence Intervals:}
Applying a two-way cluster bootstrap across 25 paired topology-seed observations ($10,000$ iterations, seed 2026) comparing Pure D3QN against OSPF (RFC 2328) yields the following headline results:
\begin{itemize}
    \item \textbf{Bottleneck Utilization Improvement:} Mean improvement of \textbf{+36.69 percentage points} ($55.25\%$ relative improvement, 95\% CI $[11.16, 62.89]$, win rate $100.0\%$).
    \item \textbf{Latency Improvement:} Mean reduction of \textbf{+115.40 ms} (95\% CI $[46.16, 183.19]$, win rate $92.0\%$).
    \item \textbf{Jitter Improvement:} Mean reduction of \textbf{+6.94 ms} (95\% CI $[2.00, 11.96]$, win rate $96.0\%$).
    \item \textbf{Packet Loss Reduction:} Mean reduction of \textbf{+3.47 percentage points} (95\% CI $[0.57, 7.11]$, win rate $100.0\%$).
    \item \textbf{Jain's Fairness Difference:} Mean difference of \textbf{-0.055} (95\% CI $[-0.133, 0.030]$, win rate $40.0\%$), confirming that the slight decrease in fairness is within the confidence interval and represents an expected operational trade-off.
    \item \textbf{Inference Time Cost:} Mean differential of \textbf{-0.220 ms} (95\% CI $[-0.296, -0.121]$), representing the modest compute cost of neural forward inference compared to static hash lookups.
\end{itemize}

\subsection{Ablation Studies: Dissecting Policy Guards and Architectural Components}
To isolate the exact contribution of each architectural innovation and evaluate deployment guards, two complementary ablation experiments were conducted:

\paragraph{1. Policy-Mode Ablation (Pure vs. Safety-Gated D3QN):}
Figure~\ref{fig:policy_ablation} compares unconstrained neural policy inference (\textbf{Pure D3QN}) against a deployment-safety variant (\textbf{Safety D3QN}) implemented in \code{controller/routing_module.py}. In Safety mode, candidate routing paths whose estimated bottleneck link utilization exceeds $\theta_{\text{safe}} = 90\%$ are dynamically masked prior to the Q-value $\arg\max$, forcing the controller to select the highest-scoring candidate among non-saturated paths. As shown across 25 paired workload-seed evaluations, Safety D3QN outperforms Pure D3QN on estimated packet loss ($0.07\%$ vs. $0.38\%$) and latency ($23.18$~ms vs. $41.53$~ms) by eliminating exploratory actions onto near-saturated links during transient policy fluctuations. While Safety mode achieves superior queue stabilization, the headline tournament results in Table~\ref{tab:tournament_results} deliberately report Pure D3QN to evaluate the core neural policy without heuristic fallback guards.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.78\textwidth]{policy_mode_ablation.png}
\caption{Policy-Mode Ablation Comparing Pure Neural D3QN Against Safety-Gated D3QN Across 25 Paired Workload-Seed Evaluations.}
\label{fig:policy_ablation}
\end{figure}

\paragraph{2. Component-Wise Architectural Ablation:}
Figure~\ref{fig:ablation_bootstrap} evaluates the step-by-step impact of individual DRL enhancements across four architectural stages: (i) Plain DQN (representing the single-stream, uniform-replay baseline of Chen et al., RL-Routing \cite{chen2020rlrouting}), (ii) Double DQN without dueling, (iii) Dueling Double DQN without PER, and (iv) Full D3QN with Prioritized Experience Replay. 

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{ablation_study_bootstrap.png}
\caption{Bootstrap Confidence Distributions of Component Ablations Across Stages: Plain DQN (Chen et al.), Double DQN, Dueling DDQN without PER, and Full D3QN.}
\label{fig:ablation_bootstrap}
\end{figure}

Quantitative metrics from the recorded ablation evaluations (\code{ablation_study_results.json}) demonstrate:
\begin{itemize}
    \item \textbf{Impact of Double Q-Learning:} Standard single-stream DQN (Chen et al. \cite{chen2020rlrouting}) exhibits significant Q-value overestimation bias under dynamic bursty traffic, resulting in a mean latency of $1114.89$~ms and $26.24\%$ loss. Introducing Double Q-learning decouples action selection from target evaluation, mitigating overestimation bias and reducing mean latency to $1060.27$~ms and loss to $23.37\%$.
    \item \textbf{Impact of Dueling Network Factorization:} Decoupling state value $V(s)$ from candidate path advantages $A(s, a)$ enables the network to identify states of general network congestion regardless of path choice. This yields the single largest performance jump: mean latency drops by over $50\%$ to $529.99$~ms, and packet loss is reduced to $15.11\%$.
    \item \textbf{Impact of Binary SumTree Prioritized Experience Replay (PER):} Uniform replay buffers dilute rare buffer-overflow and link-saturation transitions in seas of nominal traffic. The binary SumTree PER engine ensures that transitions with high TD error magnitude $\delta_i$ are sampled proportionally with $O(\log N)$ algorithmic complexity, accelerating training stability and preventing the agent from unlearning defensive rerouting under severe congestion bursts.
\end{itemize}

\subsection{Extreme Stress Testing: Jamming and Burst Avalanches}
Figure~\ref{fig:stress_test} and Figure~\ref{fig:blind_stress} evaluate platform resilience under severe core link jamming ($95\%$ saturation) and 500-flow concurrent burst avalanches.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{stress_test_load_balancing.png}
\caption{Extreme Stress Testing Under Asymmetric Core Jamming and Avalanche Bursts.}
\label{fig:stress_test}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{blind_topologies_stress_benchmark.png}
\caption{Stress Benchmarks Across Irregular and Complex Topologies.}
\label{fig:blind_stress}
\end{figure}

In the displayed stress scenario, the model reports high OSPF loss and preferential D3QN use of available bypass paths. This is a scenario-specific simulator result; it does not establish 100\% rerouting or zero-loss behavior under arbitrary failures and bursts.

\subsection{Zero-Shot Generalization on Unseen Random Topologies}
To evaluate topological invariance, the D3QN agent trained exclusively on Fat-Tree Clos was deployed directly---with \textbf{zero retraining or fine-tuning}---on three completely unvisited synthetic random graphs: a 12-node Erd\H{o}s-R\'{e}nyi graph, a 14-node Watts-Strogatz small-world graph, and a 16-node Barab\'{a}si-Albert scale-free network, as illustrated in Figure~\ref{fig:random_blind}.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{random_blind_topologies_evaluation.png}
\caption{Zero-Shot Transfer Learning Evaluation on Three Unseen Random Graphs (12-Node Erd\H{o}s-R\'{e}nyi, 14-Node Watts-Strogatz, and 16-Node Barab\'{a}si-Albert).}
\label{fig:random_blind}
\end{figure}

On the sampled random-graph workloads, the reported transfer evaluation favors D3QN over the displayed static baselines. This is empirical evidence limited to the generated synthetic graphs, traffic model, and fixed candidate-path representation; it does not prove general independence from arbitrary graph scale or permutation-invariant graph generalization.

\subsection{Comparison Against Theoretical Optimal HiGHS MILP Solver}
To establish an exact theoretical reference bound, the Unsplittable Multi-Commodity Flow (UMCF) problem was formulated as a mixed-integer linear program (MILP) and solved to global optimality using the HiGHS branch-and-cut solver via \code{scipy.optimize.milp} (\code{experiment_phase1_suite.py}).

\paragraph{MILP Optimization Formulation:}
Given active commodities $\mathcal{K}$ with bandwidth demands $d_k$, candidate path sets $\mathcal{P}_k$, and directional edge capacities $C_e$:
\begin{align}
\min_{\alpha, \mathbf{x}} \quad & \alpha \\
\text{subject to} \quad & \sum_{p \in \mathcal{P}_k} x_{k, p} = 1 \quad \forall k \in \mathcal{K} \label{eq:milp_choice} \\
& \sum_{k \in \mathcal{K}} \sum_{p \in \mathcal{P}_k : e \in p} d_k x_{k, p} \le \alpha \cdot C_e \quad \forall e \in E \label{eq:milp_cap} \\
& x_{k, p} \in \{0, 1\} \quad \forall k \in \mathcal{K}, \, p \in \mathcal{P}_k, \quad 0 \le \alpha \le 5.0
\end{align}
Constraint~(\ref{eq:milp_choice}) enforces unsplittable single-path assignment. Constraint~(\ref{eq:milp_cap}) minimizes the global maximum link utilization multiplier $\alpha$. Solver feasibility and optimality tolerances were configured to $10^{-6}$. In all benchmark evaluations, HiGHS terminated with \code{status = 0}, verifying that $\alpha^*$ represents the proven global optimum under the candidate path sets.

Figure~\ref{fig:oracle_gap} illustrates the optimality gap comparisons across benchmark fabrics.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{optimisation_oracle_gap.png}
\caption{Optimality Gap Between D3QN and the Exact HiGHS MILP Solver.}
\label{fig:oracle_gap}
\end{figure}

\paragraph{Quantitative Gaps and Computational Complexity:}
From the empirical results stored in \code{optimisation_oracle_results.json}:
\begin{itemize}
    \item \textbf{Hierarchical Tree (7 Switches, 20 Flows):} The proven theoretical optimal peak load is $\alpha^* = 47.39\%$. Static Dijkstra SPF produces a peak utilization of $98.46\%$ (an optimality gap of $107.76\%$), while ECMP induces severe congestion at $112.87\%$ (gap of $138.16\%$). In contrast, D3QN achieves a peak load of \textbf{78.74\%} (gap of \textbf{66.15\%}), closing the optimality gap relative to Dijkstra SPF by \textbf{41.61 percentage points}.
    \item \textbf{NSFNet Continental Mesh (14 Switches, 20 Flows):} The theoretical optimum is $\alpha^* = 14.28\%$. D3QN achieves a peak utilization of \textbf{20.69\%} (gap of $44.89\%$), matching Dijkstra SPF while providing proactive bypass headroom.
    \item \textbf{Scope and Like-for-Like Context:} It is important to emphasize that the MILP formulation minimizes solely the peak link utilization ($\alpha$) over candidate paths on a restricted 20-flow static demand matrix, whereas D3QN optimizes a multi-objective reward (balancing delay, jitter, loss, and hop penalties alongside congestion) across a dynamic 150-flow tournament. Consequently, the MILP solver serves as an illustrative static reference ceiling rather than a direct algorithmic parity benchmark.
    \item \textbf{Execution Latency Trade-off:} In the recorded 20-flow instances, HiGHS required $61.65$--$107.59$~ms while the D3QN forward pass required $0.24$~ms in the same software environment. Neural inference scales with fixed tensor dimensions for the configured four-action model, but end-to-end control latency also includes telemetry polling, candidate generation, and OpenFlow rule installation.
\end{itemize}

\subsection{High-Availability Controller Failover Benchmarks}
Figure~\ref{fig:ha_dashboard} depicts the live operational web management dashboard displaying real-time topology status, link rates, and active controller pool health.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{dashboard_upper_panoramic.png}
\caption{Panoramic View of the Real-Time Operational Web Telemetry Dashboard.}
\label{fig:ha_dashboard}
\end{figure}

The high-availability architecture operates a 3-node controller pool (Primary on port \code{6633}, Hot-Standby Backup 1 on \code{6634}, Hot-Standby Backup 2 on \code{6635}). Under empirical failure injection, performance is evaluated across two critical failure regimes:

\paragraph{Single and Cascaded Node Failures:}
When an active controller node crashes (simulating hardware fault or process termination):
\begin{itemize}
    \item \textbf{Internal Active Pointer Promotion Bookkeeping:} \textbf{0.001 ms} (1.0~$\mu$s CPU memory pointer reassignment and event logging in the local master-slave pool).
    \item \textbf{End-to-End Client HTTP REST API Recovery Time:} \textbf{37.96 ms} (transparent client HTTP retry catching socket connection refusal and redirecting to the standby endpoint).
    \item \textbf{Process Crash-to-Promotion Cascade:} \textbf{41.62--69.77 ms} (Primary $\to$ Backup 1) and \textbf{38.68--45.28 ms} (Backup 1 $\to$ Backup 2 cascaded double fault).
    \item \textbf{Failure Detection Window:} For hung or unresponsive controller processes (as opposed to immediate socket resets), watchdog heartbeat detection operates with a configurable timeout $T_{\text{detect}} \le 1.0$~second.
    \item \textbf{Data-Plane Packet Continuity:} In-flight packet loss during the control-plane transition gap was not directly instrumented on live packet traces; however, because Open vSwitch switches operate in \textbf{Fail-Secure Mode} (\code{fail_mode=secure}), switches retain committed flow table entries in kernel TCAM tables, allowing existing matching traffic to forward without interruption during control failover.
\end{itemize}

\paragraph{Total Cluster Outage Handling (What Happens When ALL Controllers Fail):}
A critical requirement of resilient network engineering is specifying behavior when all controllers in the cluster fail simultaneously (e.g., complete control-plane partition or multi-node power outage). In this platform:
\begin{enumerate}
    \item \textbf{OpenFlow Fail-Secure Autonomous Survival Mode:} OpenFlow switches transition automatically from active OpenFlow management to \textbf{Fail-Secure Mode} (\code{fail_mode=secure}). The switch kernel datapath does not purge existing flow entries upon control connection loss.
    \item \textbf{In-Flight Data-Plane Continuity:} Packets matching existing flow rules continue to be switched and forwarded at full line rate by the kernel datapath, sustaining forwarding continuity for active TCP connections and existing real-time streams.
    \item \textbf{Dynamic Route Update Suspension:} Dynamic D3QN rerouting and new flow setup computations are temporarily paused, since no active controller is available to process OpenFlow \code{OFPT_PACKET_IN} events. Unmatched new packets are queued or dropped locally at the edge rather than causing network loops.
    \item \textbf{Autonomous Self-Healing Cluster Recovery:} Background watchdog health probers continuously monitor controller socket availability. As soon as any controller node recovers (e.g., Primary reboot), the pool dynamically promotes the restored node, re-establishes OpenFlow control sessions, resumes real-time telemetry polling, and re-enables closed-loop D3QN route optimization without requiring manual network intervention.
\end{enumerate}

\subsection{Critical Discussion: Operational Trade-offs and Computational Costs}
While the empirical results demonstrate clear superiority over static heuristics, deploying DRL in production telecommunication networks entails concrete operational trade-offs:
\begin{enumerate}
    \item \textbf{Inference Latency vs. Metric Freshness:} The forward pass requires $0.216$--$0.279$~ms on commodity CPUs. While well within line-rate bounds for flow setup, the polling interval $\Delta t = 1.0$~s introduces a 1-second lag in counter updates. Reducing $\Delta t < 100$~ms increases controller control-channel overhead.
    \item \textbf{Offline Training Requirement:} The D3QN agent requires approximately 3,000 steps of offline training on simulated or emulated traffic traces to achieve convergence. Cold-starting an untrained agent directly on live production links is prohibited due to exploratory packet drops.
    \item \textbf{Switch Flow Table TCAM Capacity:} Dynamic per-flow rule installation consumes OpenFlow switch TCAM entries. On enterprise hardware with limited TCAM (e.g., 2,000 flow rules), wild-card flow aggregation or elephant-flow filtering must be employed.
\end{enumerate}

\subsection{Threats to Validity and Mitigation Strategies}
\begin{itemize}
    \item \textbf{Internal Validity:} Verified through deterministic random seeding, automated 42-test continuous integration, and identical background traffic conditions across baseline comparisons.
    \item \textbf{Construct Validity:} Key performance indicators follow standard IETF IPPM specifications: RFC 2679 for one-way delay, RFC 2680 for packet loss, and RFC 3393 for packet delay variation (jitter). Baseline routing protocol mechanics are benchmarked against RFC 2328 (OSPF v2).
    \item \textbf{External Validity:} Evaluated across five diverse topologies and generalized to random small-world graphs. Hardware ASIC testing on Barefoot Tofino is identified as the next evolutionary step.
\end{itemize}
'''
