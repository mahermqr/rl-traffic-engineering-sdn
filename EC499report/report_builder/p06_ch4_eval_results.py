# Chapter 4: The Proposed System (Part 2 - Testing & Evaluation, Results & Discussion)

CHAPTER_4_EVAL_RESULTS = r'''% ----------------------------------------------------------------------------
% 4.3 TESTING AND EVALUATION
% ----------------------------------------------------------------------------
\section{Testing and Evaluation}
\label{sec:testing}

\subsection{Key Performance Metrics}
The software-model study uses the following metrics. Packet-emulation measurements are defined separately in Section~\ref{sec:mininet_eval}:
\begin{enumerate}
    \item \textbf{Bottleneck Utilization:} The tournament reports the mean of sampled per-path bottleneck utilizations; peak network load is a different statistic (\lowerbetter).
    \item \textbf{End-to-End Latency ($D$):} Mean packet transit delay in milliseconds (\lowerbetter).
    \item \textbf{Modelled Jitter Proxy ($J$):} A bounded queue-delay and utilization-based heuristic in milliseconds (\lowerbetter).
    \item \textbf{Packet Drop Rate ($P_{\text{loss}}$):} Percentage of transmitted packets dropped due to buffer overflow (\lowerbetter).
    \item \textbf{Jain's Fairness Index ($\mathcal{J}$):} In the tournament, applies the Jain formula to sampled path-bottleneck utilizations, rather than measured per-flow throughput \cite{jain1984quantitative} (where higher values indicate more balanced load distribution, $\higherbetter$):
    \begin{equation}
    \label{eq:jains_fairness_metric}
    \mathcal{J} = \frac{\left( \sum_{k=1}^K x_k \right)^2}{K \sum_{k=1}^K x_k^2}.
    \end{equation}
    \item \textbf{High-Availability Failover Latency ($\tau_{\text{fail}}$):} Milliseconds required to promote a standby controller and resume client HTTP REST service (\lowerbetter).
\end{enumerate}

\subsection{Test Procedures and Recorded Data}
The checks address three different aspects of the completed system. Functional tests exercise the software interfaces and data structures; the software-model comparisons examine routing decisions under controlled synthetic conditions; and Mininet runs real traffic through a software forwarding plane. Controller HTTP recovery is measured separately.

For each Mininet condition, the runner starts a fresh controller and network, launches the background stream, performs an unscored transport warm-up, records ping output, and runs the measured iperf transfer. The matrix uses Tree and Fat-Tree networks, SPF/LLR/D3QN policies, TCP/UDP, and ten repeats per condition. The default measured transfer lasts 15~s, UDP offered rate is 65~Mbps, background rate is 45~Mbps, and configured warm-up is 4~s. The timed background stream begins before warm-up and ping, so it does not necessarily cover the entire measured transfer. Table~\ref{tab:test_outputs} categorizes the validation checks, experimental procedures, and recorded artifact formats produced across the evaluation phases.

\begin{table}[htbp]
\centering
\caption{Tests and Recorded Outputs}
\label{tab:test_outputs}
\small
\begin{tabularx}{\textwidth}{p{3.0cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X}
\toprule
Check & Procedure or equipment & Recorded output \\
\midrule
Software functions & \code{EC499tests/test_suite.py} & Named pass/fail checks for the covered behaviours. \\
Model routing & Seeded graph and traffic fixtures & Routing-result JSON and corresponding figures. \\
Packet forwarding & Mininet, Open vSwitch, iperf, and ping & Trial conditions; raw client/server CSVs; ping text; OVS flow/port dumps; controller logs. \\
HTTP recovery & Active/standby endpoint pool and injected endpoint failure & Selection history and client recovery timing. \\
\bottomrule
\end{tabularx}
\end{table}

The final packet run is identified as \code{mininet_20261026T173329Z_seed2026}. Its trial manifest, environment record, and raw outputs are retained with the delivery. Analysis files contain the condition summaries and confidence intervals used in the result tables. Appendix~\ref{app:manual} gives the commands for repeating the tests.

\subsection{Automated Test Suite and Functional Verification}
To check selected software behavior, the platform includes a 42-test automated unit, integration, and failover test suite (\code{test_suite.py}). The suite verifies:
\begin{itemize}
    \item Neural model weight lifecycle, Polyak soft updates, and dueling aggregation identifiability.
    \item Binary SumTree priority insertion, proportional sampling, and $O(\log N)$ arithmetic.
    \item Active/standby pool initialization, cascaded local failover bookkeeping, endpoint formatting, and API-level behavior. The suite does not implement or validate Raft consensus, quorum election, or OpenFlow reconnection timing.
    \item REST API mutations, topology discovery, and dynamic link failure rerouting.
\end{itemize}
The checked-in suite contains 42 tests. Runtime is environment-dependent and should be reported from the delivery machine rather than treated as a performance result.

\subsection{Checks Against the Project Objectives}
Table~\ref{tab:claim_evidence} links the implemented functions to the checks and results used to assess them.

\begin{table}[htbp]
\centering
\caption{Project Functions and Supporting Checks}
\label{tab:claim_evidence}
\scriptsize
\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash\bfseries}p{2.6cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}p{4.2cm} >{\raggedright\arraybackslash}p{3.4cm}}
\toprule
\textbf{Engineering Claim} & \textbf{Verified Architectural Mechanism} & \textbf{Source File} & \textbf{Empirical Evidence} \\
\midrule
Bottleneck Load Reduction & D3QN + thresholded quadratic congestion term & \code{controller/routing_module.py} & Table~\ref{tab:tournament_results}: $79.1\%$ reduction on Spine-Leaf ($99.84\% \to 20.89\%$; $53.9\%$ reduction in the five-fabric arithmetic mean) \\
Packet Loss Suppression & Proactive Bypass Rerouting & \code{controller/routing_module.py} & Final seed-42 model run: $0.45\%$ mean estimated loss vs $4.13\%$ OSPF; four entries round to $0.000\%$ \\
Jitter Suppression & Modelled Jitter Penalty in Reward & \code{controller/routing_module.py} & Table~\ref{tab:tournament_results}: $0.515$~ms vs $15.50$~ms on Spine-Leaf (mean $71.1\%$ suppression across 5 fabrics: $2.71$~ms vs $9.39$~ms OSPF) \\
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

\subsection{Final Software-Model Routing Comparison}
Table~\ref{tab:tournament_results} presents the quantitative results of the routing tournament across all five benchmark topologies under heavy traffic loads. The \textbf{Offload (\%)} column quantifies the Congestion Offload Efficiency $\eta_{\text{offload}} = \frac{N_{\text{rerouted}}}{N_{\text{total}}} \times 100\%$, counting sampled paths that differ from the first generated candidate path used as the benchmark reference. It does not establish edge disjointness or directly measure bytes offloaded.

\begin{table}[htbp]
\centering
\caption{Final Software-Model Results Across Five Topologies (Seed-42 Snapshot; see Section~\ref{sec:multiseed_anova} for 125-Case Variance Decomposition)}
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
    \item \textbf{Topology-Dependent Trade-offs:} On Tree, D3QN has higher modelled latency and jitter than Dijkstra SPF and ECMP, and higher bottleneck utilization. Its modelled loss is lower than Dijkstra but higher than ECMP, and its reported Jain index is higher than both. The fixture includes mesh bypass links, so the result cannot be explained by assuming every flow must cross the root.
    \item \textbf{Estimated Packet Loss:} OSPF has an arithmetic mean estimated loss of $4.13\%$, while D3QN has $0.45\%$ in this run. Four D3QN table entries round to $0.000\%$; these are model outputs, not direct hardware measurements.
    \item \textbf{Jain's Fairness Trade-Off:} D3QN exhibits a lower arithmetic mean Jain's Fairness Index (\textbf{0.6972}) than OSPF (\textbf{0.7677}) in this run. This is a trade-off in the benchmark's path-utilization dispersion statistic; it does not establish a change in measured per-flow bandwidth fairness.
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

\subsection{Final Mininet Packet-Test Results}
\label{sec:mininet_eval}
A separate 120-trial packet test was completed in Linux network namespaces using Mininet and Open vSwitch with OpenFlow 1.3 (\code{EC499tests/reproduce_mininet_packet_experiment.py}).

The factorial design evaluated:
\begin{itemize}
    \item \textbf{Topologies ($2$):} Fat-Tree Clos (20 switches, rich multipath core) and Hierarchical Tree with mesh bypass links (7 switches).
    \item \textbf{Protocols ($2$):} TCP (the run does not record the active congestion-control algorithm) and UDP (constant bit-rate stress traffic).
    \item \textbf{Routing Policies ($3$):} Proposed D3QN (closed-loop neural control), Least-Loaded Routing (LLR heuristic), and hop-count Shortest Path First (SPF).
    \item \textbf{Replicates ($10$):} 10 fresh-network runs per condition on the same host with randomized execution order ($2 \times 2 \times 3 \times 10 = 120$ trials, $100\%$ completion rate, seed 2026).
\end{itemize}

Every trial recorded \code{iperf} throughput, UDP datagram loss and jitter, ICMP round-trip time and echo loss, Open vSwitch statistics, and controller decision overhead. TCP \code{iperf2} did not expose a retransmission or transport-loss field, so ICMP echo loss is reported separately and must not be interpreted as TCP packet loss. Tables~\ref{tab:mininet_measured_summary} and~\ref{tab:mininet_diagnostics} present condition-level means with non-parametric $10,000$-iteration bootstrap $95\%$ confidence intervals computed directly by \code{analyze_mininet_measured_trials.py}. Figure~\ref{fig:mininet_measured_trials} plots the measured transport throughput and UDP datagram loss condition means across policies and topologies. RTT means use the successful echo samples; trials with 100\% ICMP echo loss correctly have no RTT observation.

\begin{table}[htbp]
\centering
\caption{Measured Transport Results: Means and 95\% Bootstrap Intervals (10 Trials per Condition)}
\label{tab:mininet_measured_summary}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\textwidth}{l c c >{\centering\arraybackslash}X >{\centering\arraybackslash}X}
\toprule
Topology & Protocol & Policy & Throughput (Mbps) & UDP datagram loss (\%) \\
\midrule
Fat-Tree & TCP & D3QN & 47.91 $[47.71,48.15]$ & --- \\
Fat-Tree & TCP & LLR & 47.83 $[47.67,48.00]$ & --- \\
Fat-Tree & TCP & SPF & 47.64 $[47.60,47.66]$ & --- \\
Fat-Tree & UDP & D3QN & 48.69 $[48.61,48.84]$ & 27.42 $[27.19,27.54]$ \\
Fat-Tree & UDP & LLR & 48.87 $[48.57,49.22]$ & 27.08 $[26.56,27.50]$ \\
Fat-Tree & UDP & SPF & 48.39 $[47.97,48.61]$ & 28.39 $[27.54,30.09]$ \\
Tree & TCP & D3QN & 34.08 $[28.56,39.62]$ & --- \\
Tree & TCP & LLR & 38.09 $[32.39,43.80]$ & --- \\
Tree & TCP & SPF & 28.56 $[28.56,28.57]$ & --- \\
Tree & UDP & D3QN & 29.31 $[29.17,29.57]$ & 55.98 $[55.78,56.18]$ \\
Tree & UDP & LLR & 31.13 $[29.18,35.02]$ & 52.79 $[47.09,55.72]$ \\
Tree & UDP & SPF & 29.18 $[29.18,29.18]$ & 55.93 $[55.72,56.06]$ \\
\bottomrule
\end{tabularx}
\end{table}

\begin{table}[htbp]
\centering
\caption{ICMP Diagnostics and Controller Decisions: Means and 95\% Bootstrap Intervals}
\label{tab:mininet_diagnostics}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\textwidth}{l c c >{\centering\arraybackslash}X >{\centering\arraybackslash}X >{\centering\arraybackslash}X}
\toprule
Topology & Protocol & Policy & RTT (ms) & ICMP echo loss (\%) & Decision time (ms) \\
\midrule
Fat-Tree & TCP & D3QN & 20.72 $[20.58,20.84]$ & 36 $[10,66]$ & 0.758 $[0.644,0.919]$ \\
Fat-Tree & TCP & LLR & 20.59 $[20.51,20.70]$ & 47 $[17,77]$ & 0.016 $[0.014,0.019]$ \\
Fat-Tree & TCP & SPF & 20.76 $[20.63,20.90]$ & 18 $[0,44]$ & 0.028 $[0.026,0.030]$ \\
Fat-Tree & UDP & D3QN & 20.55 $[20.48,20.64]$ & 14 $[0,33]$ & 0.661 $[0.621,0.704]$ \\
Fat-Tree & UDP & LLR & 20.74 $[20.51,21.11]$ & 17 $[0.98,39]$ & 0.015 $[0.014,0.017]$ \\
Fat-Tree & UDP & SPF & 20.75 $[20.52,21.09]$ & 25 $[0,50]$ & 0.027 $[0.024,0.029]$ \\
Tree & TCP & D3QN & 32.41 $[29.94,35.68]$ & 10 $[0,30]$ & 0.554 $[0.519,0.593]$ \\
Tree & TCP & LLR & 32.21 $[28.58,36.63]$ & 0 $[0,0]$ & 0.013 $[0.012,0.014]$ \\
Tree & TCP & SPF & 32.62 $[32.50,32.74]$ & 10 $[0,30]$ & 0.021 $[0.020,0.023]$ \\
Tree & UDP & D3QN & 32.30 $[31.83,32.57]$ & 10 $[0,30]$ & 0.523 $[0.500,0.552]$ \\
Tree & UDP & LLR & 35.25 $[30.95,40.96]$ & 3 $[0,9]$ & 0.013 $[0.012,0.014]$ \\
Tree & UDP & SPF & 32.84 $[32.50,33.29]$ & 2 $[0,6]$ & 0.021 $[0.019,0.023]$ \\
\bottomrule
\end{tabularx}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.88\textwidth]{mininet_measured_trials.png}
\caption{Measured Mininet condition means (120 trials): \code{iperf} throughput and UDP datagram loss across policies and topologies. Note: TCP retransmissions were uninstrumented in the test harness; ICMP echo loss is reported separately as an out-of-band diagnostic of concurrent reachability under saturation and must not be conflated with TCP transport-layer packet loss. Detailed bootstrap confidence intervals and controller overhead diagnostics appear in Tables~\ref{tab:mininet_measured_summary} and~\ref{tab:mininet_diagnostics}.}
\label{fig:mininet_measured_trials}
\end{figure}

Key empirical findings from the 120-trial Mininet emulation include:
\begin{enumerate}
    \item \textbf{Fat-Tree UDP: modest advantage over SPF, not over LLR.} Paired by replicate, D3QN improves throughput over SPF by $0.291$~Mbps (95\% CI $[0.003,0.715]$) and reduces UDP datagram loss by $0.970$ percentage points (95\% CI $[0.005,2.669]$). Against LLR, D3QN's throughput difference is inconclusive and its datagram loss is $0.346$ points higher (95\% CI for the LLR advantage $[0.040,0.679]$).
    \item \textbf{Tree results are variable and do not establish dominance.} Under TCP, D3QN's mean throughput is $34.08$~Mbps versus $28.56$~Mbps for SPF and $38.09$~Mbps for LLR. The paired D3QN--SPF interval nearly includes zero ($[-0.0003,11.050]$~Mbps), while the D3QN--LLR interval spans both signs ($[-11.635,5.123]$~Mbps). Under UDP, D3QN and SPF have nearly identical throughput and datagram loss within paired confidence intervals.
    \item \textbf{ICMP loss is diagnostic, not TCP transport loss.} Echo loss varies widely on Fat-Tree TCP (means $18$--$47\%$ with broad intervals), but TCP retransmissions were not instrumented. These values therefore describe concurrent ICMP reachability under load and do not support a route-flapping or TCP-loss causal claim.
    \item \textbf{Controller overhead profiling.} D3QN decision latency averages $0.52$--$0.76$~ms, compared with $0.013$--$0.028$~ms for the two deterministic policies. This is small relative to the tested flow durations, but production suitability would require hardware-specific load and tail-latency validation.
\end{enumerate}

\subsection{Traffic Load Scaling and Congestion Transition}
Figure~\ref{fig:traffic_load_scaling} illustrates network performance across scaled traffic injection rates ($10$~Mbps to $100$~Mbps).

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{traffic_load_scaling_curves.png}
\caption{Traffic Load Scaling Curves Demonstrating Modelled Congestion Response.}
\label{fig:traffic_load_scaling}
\end{figure}

In the plotted model, static protocols show a sharp latency increase above approximately $70$~Mbps as queues fill. The thresholded congestion term (\ref{eq:barrier_function}) and path selection reduce this increase in the tested scenario; the plot does not establish a universal flat-latency guarantee.

\subsection{Model-Seed and Workload Checks}
The additional software-model checks examine sensitivity to model seed, workload seed, and topology across 125 crossed cases:
\begin{equation}
\label{eq:eval_sample_space}
N_{\text{eval}} = 5\ \text{model seeds} \times 5\ \text{workload seeds} \times 5\ \text{topologies} = 125.
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

\paragraph{Descriptive variance components:}
\label{sec:multiseed_anova}
The stored descriptive variance decomposition (\code{multiple_model_seeds_results.json}) reports main-factor sums of squares for initialization seed, workload seed, and topology. Interactions are absorbed into a residual; the analysis does not establish causal attribution or seed equivalence:
\begin{itemize}
    \item \textbf{Bottleneck Utilization Variance:} Network topology geometry accounts for \textbf{93.51\%} of total variance. In contrast, model initialization seed accounts for only \textbf{0.73\%} of total variance , and workload seed accounts for \textbf{0.02\%}, with residual error at \textbf{5.74\%}. The stored artifact contains descriptive variance components, but no corresponding F-test or p-value. Because the benchmark topologies differ fundamentally in graph diameter, nodal degree, and bisection bandwidth, topology geometry naturally accounts for $93.51\%$--$98.53\%$ of total variance, while the seed component is below $1\%$ for these congestion and loss metrics; other metrics can be more seed-sensitive.
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
    \item \textbf{Jain's Fairness Difference:} Mean difference of \textbf{-0.055} (95\% CI $[-0.133, 0.030]$, win rate $40.0\%$), whose interval includes both signs; the data do not establish a consistent direction for this statistic.
    \item \textbf{Inference Time Cost:} Mean differential of \textbf{-0.220 ms} (95\% CI $[-0.296, -0.121]$), representing the modest compute cost of neural forward inference compared to static hash lookups.
\end{itemize}

\subsection{Checks of Policy Mode and Network Components}
Two software-model comparisons check the effect of policy mode and of individual learning components:

\paragraph{1. Policy-Mode Ablation (Pure vs. Safety-Gated D3QN):}
Figure~\ref{fig:policy_ablation} compares pure D3QN with the heuristic \code{safety} mode in \code{controller/policy_selector.py}. Safety mode normalizes Q-values and subtracts a cost based on projected utilization above 70\%, delay, loss, and hops. It does not hard-mask routes above a 90\% threshold or guarantee capacity feasibility. The archived model comparison reports estimated loss of $0.07\%$ versus $0.38\%$ and latency of $23.18$ versus $41.53$~ms. These values describe that archived configuration; its outcome is distinct from pure-D3QN tournament and packet results.
\begin{figure}[htbp]
\centering
\includegraphics[width=0.78\textwidth]{policy_mode_ablation.png}
\caption{Policy-Mode Ablation Comparing Pure Neural D3QN Against Safety-Gated D3QN Across 25 Paired Workload-Seed Evaluations.}
\label{fig:policy_ablation}
\end{figure}

\paragraph{2. Component-Wise Architectural Ablation:}
Figure~\ref{fig:ablation_bootstrap} evaluates the step-by-step impact of individual DRL enhancements across four architectural stages: (i) Plain DQN (a local single-stream, uniform-replay baseline), (ii) Double DQN without dueling, (iii) Dueling Double DQN without PER, and (iv) Full D3QN with Prioritized Experience Replay. 

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{ablation_study_bootstrap.png}
\caption{Bootstrap Confidence Distributions of Component Ablations Across Stages: Local Plain DQN, Double DQN, Dueling DDQN without PER, and Full D3QN.}
\label{fig:ablation_bootstrap}
\end{figure}

Quantitative metrics from the recorded ablation evaluations (\code{ablation_study_results.json}) demonstrate:
\begin{itemize}
    \item \textbf{Impact of Double Q-Learning:} The local standard-DQN baseline reports a mean latency of $1114.89$~ms and $26.24\%$ loss. Introducing Double Q-learning decouples action selection from target evaluation, mitigating overestimation bias and reducing mean latency to $1060.27$~ms and loss to $23.37\%$.
    \item \textbf{Impact of Dueling Network Factorization:} Decoupling state value $V(s)$ from candidate path advantages $A(s, a)$ enables the network to identify states of general network congestion regardless of path choice. This yields the single largest performance jump: mean latency drops by over $50\%$ to $529.99$~ms, and packet loss is reduced to $15.11\%$.
    \item \textbf{Impact of Binary SumTree Prioritized Experience Replay (PER):} Uniform replay buffers dilute rare buffer-overflow and link-saturation transitions amid predominantly uncongested nominal traffic samples. The binary SumTree PER engine ensures that transitions with high TD error magnitude $\delta_i$ are sampled proportionally with $O(\log N)$ algorithmic complexity, accelerating training stability and changing transition sampling frequency; this mechanism alone does not prove convergence or prevention of forgetting.
\end{itemize}

\subsection{Stress-Test Results}
Figure~\ref{fig:stress_test} and Figure~\ref{fig:blind_stress} evaluate platform resilience under severe core link saturation ($95\%$ capacity) and 500-flow concurrent synchronized traffic bursts.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{stress_test_load_balancing.png}
\caption{Stress Testing Under Asymmetric Core Link Saturation and Synchronized High-Concurrency Bursts.}
\label{fig:stress_test}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{blind_topologies_stress_benchmark.png}
\caption{Stress Benchmarks Across Irregular and Complex Topologies.}
\label{fig:blind_stress}
\end{figure}

In the displayed stress scenario, the model reports high OSPF loss and preferential D3QN use of available bypass paths. This is a scenario-specific simulator result; it does not establish 100\% rerouting or zero-loss behavior under arbitrary failures and bursts.

\clearpage
\subsection{Transfer Checks on Unseen Random Topologies}
To check transfer within the sampled graph set, the D3QN agent trained exclusively on Fat-Tree Clos was deployed directly---with \textbf{zero retraining or fine-tuning}---on three previously unseen synthetic random graph topologies: a 12-node Erd\H{o}s-R\'{e}nyi graph, a 14-node Watts-Strogatz small-world graph, and a 16-node Barab\'{a}si-Albert scale-free network, as illustrated in Figure~\ref{fig:random_blind}.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.80\textwidth]{random_blind_topologies_evaluation.png}
\caption{Zero-Shot Transfer Learning Evaluation on Three Unseen Random Graphs (12-Node Erd\H{o}s-R\'{e}nyi, 14-Node Watts-Strogatz, and 16-Node Barab\'{a}si-Albert).}
\label{fig:random_blind}
\end{figure}

On the sampled random-graph workloads, the reported transfer evaluation favors D3QN over the displayed static baselines. This is empirical evidence limited to the generated synthetic graphs, traffic model, and fixed candidate-path representation; it does not prove general independence from arbitrary graph scale or permutation-invariant graph generalization.

\subsection{Comparison with a Small Optimisation Reference}
To establish an exact theoretical reference bound, the Unsplittable Multi-Commodity Flow (UMCF) problem was formulated as a mixed-integer linear program (MILP) and solved to global optimality using the HiGHS branch-and-cut solver via \code{scipy.optimize.milp} (\code{experiment_phase1_suite.py}).

\paragraph{MILP Optimization Formulation:}
Given active commodities $\mathcal{K}$ with bandwidth demands $d_k$, candidate path sets $\mathcal{P}_k$, and directional edge capacities $C_e$:
\begin{align}
\min_{\alpha, \mathbf{x}} \quad & \alpha \notag \\
\text{subject to} \quad & \sum_{p \in \mathcal{P}_k} x_{k, p} = 1 \quad \forall k \in \mathcal{K} \label{eq:milp_choice} \\
& \sum_{k \in \mathcal{K}} \sum_{p \in \mathcal{P}_k : e \in p} d_k x_{k, p} \le \alpha \cdot C_e \quad \forall e \in E \label{eq:milp_cap} \\
& x_{k, p} \in \{0, 1\} \quad \forall k \in \mathcal{K}, \, p \in \mathcal{P}_k, \quad 0 \le \alpha \le 5.0 \notag
\end{align}
Constraint~(\ref{eq:milp_choice}) enforces unsplittable single-path assignment. Constraint~(\ref{eq:milp_cap}) minimizes the global maximum link utilization multiplier $\alpha$. Solver feasibility and optimality tolerances were configured to $10^{-6}$. In all benchmark evaluations, the implementation accepts a solver result only when \code{status = 0}; the summary does not retain each solver certificate. Within those restricted instances, $\alpha^*$ represents the proven global optimum under the candidate path sets.

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
    \item \textbf{NSFNet Continental Mesh (14 Switches, 20 Flows):} The theoretical optimum is $\alpha^* = 14.28\%$. D3QN achieves a peak utilization of \textbf{20.69\%} (gap of $44.89\%$), matching Dijkstra SPF while under the same reported utilization objective.
    \item \textbf{Methodological Comparability and Scope Discrepancy:} It is important to emphasize that the MILP formulation minimizes solely the peak link utilization ($\alpha$) over candidate paths on a restricted 20-flow static demand matrix, whereas D3QN optimizes a multi-objective reward (balancing delay, jitter, loss, and hop penalties alongside congestion) across a dynamic 150-flow tournament. Consequently, the MILP solver serves as an illustrative static reference ceiling for the separately evaluated 20-flow instances. The 150-flow tournament must not be treated as a matched oracle comparison.
    \item \textbf{Execution Latency Trade-off:} In the recorded 20-flow instances, HiGHS required $61.65$--$107.59$~ms while the D3QN forward pass required $0.24$~ms in the same software environment. Neural inference scales with fixed tensor dimensions for the configured four-action model, but end-to-end control latency also includes telemetry polling, candidate generation, and OpenFlow rule installation.
\end{itemize}

\subsection{Active/Standby Controller Pool Failover Benchmarks}
Figure~\ref{fig:ha_dashboard} depicts the live operational web management dashboard displaying real-time topology status, link rates, and active controller pool health.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{dashboard_upper_panoramic.png}
\caption{Panoramic View of the Real-Time Operational Web Telemetry Dashboard.}
\label{fig:ha_dashboard}
\end{figure}

The redundancy architecture operates a 3-node active/standby controller pool (Primary on port \code{6633}, Standby Backup 1 on \code{6634}, Standby Backup 2 on \code{6635}). Under empirical failure injection, performance is evaluated across two critical failure regimes:

\paragraph{Single and Cascaded Node Failures:}
When an active controller node crashes (simulating hardware fault or process termination):
\begin{itemize}
    \item \textbf{Internal Active Pointer Promotion Bookkeeping:} \textbf{0.001 ms} (1.0~$\mu$s CPU memory pointer reassignment and event logging in the local master-slave pool).
    \item \textbf{End-to-End Client HTTP REST API Recovery Time:} \textbf{37.96 ms} (transparent client HTTP retry catching socket connection refusal and redirecting to the standby endpoint).
    \item \textbf{Process Crash-to-Promotion Cascade:} \textbf{41.62--69.77 ms} (Primary $\to$ Backup 1) and \textbf{38.68--45.28 ms} (Backup 1 $\to$ Backup 2 cascaded double fault).
    \item \textbf{Failure Detection Window:} For hung or unresponsive controller processes (as opposed to immediate socket resets), watchdog heartbeat detection operates with a configurable timeout $T_{\text{detect}} \le 1.0$~second.
    \item \textbf{Data-Plane Packet Continuity:} In-flight packet loss during the control-plane transition gap was not directly instrumented on live packet traces; however, because Open vSwitch switches operate in \textbf{Fail-Secure Mode} (\code{fail_mode=secure}), switches retain committed flow table entries in software flow tables, allowing matching traffic to continue while entries remain valid. This potential behavior was not established as uninterrupted forwarding by the HTTP test.
\end{itemize}

\paragraph{Total Cluster Outage Handling (What Happens When ALL Controllers Fail):}
A critical requirement of resilient network engineering is specifying behavior when all controllers in the cluster fail simultaneously (e.g., complete control-plane partition or multi-node power outage). In this platform:
\begin{enumerate}
    \item \textbf{OpenFlow Fail-Secure Autonomous Survival Mode:} OpenFlow switches transition automatically from active OpenFlow management to \textbf{Fail-Secure Mode} (\code{fail_mode=secure}). The switch kernel datapath does not purge existing flow entries upon control connection loss.
    \item \textbf{Existing-Rule Forwarding:} Matching packets can continue through the software datapath while entries remain installed; idle and hard timeouts still apply. Continuity during failover was not measured with packet traces.
    \item \textbf{Dynamic Route Update Suspension:} Dynamic D3QN rerouting and new flow setup computations are temporarily paused, since no active controller is available to process OpenFlow \code{OFPT_PACKET_IN} events. Unmatched new packets are queued or dropped locally at the edge rather than causing network loops.
    \item \textbf{Autonomous Self-Healing Cluster Recovery:} Background watchdog health probers continuously monitor controller socket availability. As soon as any controller node recovers (e.g., Primary reboot), the pool can select a healthy endpoint again. OpenFlow reconnection, state consistency, and routing recovery require separate verification.
\end{enumerate}

\subsection{Practical Limitations}
The results show workload-dependent advantages and limitations; deploying DRL in production telecommunication networks entails concrete operational trade-offs:
\begin{enumerate}
    \item \textbf{Inference Latency vs. Metric Freshness:} The forward pass requires $0.216$--$0.279$~ms on the tested CPU. This is small relative to the evaluated flow timescale, but the polling interval ($\Delta t = 1.0$~s in high-frequency test mode, and $\Delta t = 3.0$~s in nominal Mininet emulation) introduces a corresponding lag in counter updates before physical telemetry reflects link load. Reducing $\Delta t < 100$~ms increases controller control-channel overhead.
    \item \textbf{Offline Training Requirement:} The D3QN agent requires approximately 3,000 steps of offline training on simulated or emulated traffic traces to achieve convergence. Cold-starting an untrained agent directly on live production links is prohibited due to exploratory packet drops.
    \item \textbf{Switch Flow Table TCAM Capacity:} Dynamic per-flow rule installation consumes OpenFlow switch TCAM entries. On enterprise hardware with limited TCAM (e.g., 2,000 flow rules), wild-card flow aggregation or elephant-flow filtering must be employed.
\end{enumerate}

\subsection{Limits on Interpreting the Results}
\begin{itemize}
    \item \textbf{Test conditions:} Supported by seeded condition order and 42 automated software tests. The packet runner launches fixed-duration background traffic before transport warm-up and ping; the background stream may therefore end before the measured iperf stream. The dataset should be interpreted as the recorded sequential workload, not constant concurrent saturation throughout every measurement.
    \item \textbf{Meaning of the measurements:} Queue-model delay/loss/jitter, iperf UDP statistics, and ICMP RTT/echo loss are distinct constructs. The experiment does not measure synchronized one-way IPPM delay or TCP retransmission loss. RFCs provide background definitions rather than a certificate of conformance for every proxy.
    \item \textbf{Scope of the findings:} Evaluated on five model fixtures and selected random graphs, with packet emulation on two fixtures. Ten repeats on one VM do not establish cross-host or production-network validity. The reported percentile intervals are exploratory and are not adjusted for multiple comparisons. Hardware ASIC testing on Barefoot Tofino is identified as the next evolutionary step.
\end{itemize}
\subsection{Chapter Summary}
The completed implementation passed the covered software checks and produced results for all 120 packet-test conditions. The model comparisons show potential congestion benefits, while the packet results show that a simple least-loaded policy remains competitive. The practical outcome is a testable routing platform with documented procedures and limitations, rather than a general guarantee that learned routing is preferable.
'''
