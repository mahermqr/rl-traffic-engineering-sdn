# `EC499report/report_builder/p09_references_appendices.py`

> **File:** `EC499report/report_builder/p09_references_appendices.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 526  
> **File Size:** 35.11 KB  

---

## Overview

References and Appendices

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
# References and Appendices

REFERENCES_AND_APPENDICES = r'''% ============================================================================
% REFERENCES
% ============================================================================
\begin{thebibliography}{99}
\addcontentsline{toc}{chapter}{References}

\bibitem[Al-Fares et al.(2008)]{al2008scalable}
Al-Fares, M., Loukissas, A., and Vahdat, A. (2008). ``A scalable, commodity data center network architecture,'' \emph{ACM SIGCOMM Computer Communication Review}, vol.~38, no.~4, pp. 63--74.

\bibitem[Al-Fares et al.(2010)]{al2010hedera}
Al-Fares, M., Radhakrishnan, S., Raghavan, B., Huang, N., and Vahdat, A. (2010). ``Hedera: Dynamic flow management for data center networks,'' in \emph{Proceedings of the 7th USENIX Conference on Networked Systems Design and Implementation (NSDI)}, pp. 19--19.

\bibitem[Almasan et al.(2022a)]{almasan2022enero}
Almasan, P., Xiao, S., Cheng, X., Shi, X., Barlet-Ros, P., and Cabellos-Aparicio, A. (2022a). ``ENERO: Efficient real-time WAN routing optimization with deep reinforcement learning,'' \emph{Computer Networks}, vol.~219, p. 109438, 2022, doi: 10.1016/j.comnet.2022.109438.

\bibitem[Almasan et al.(2022b)]{almasan2022gnn}
Almasan, P., Su\'{a}rez-Varela, J., Rusek, K., Barlet-Ros, P., and Cabellos-Aparicio, A. (2022b). ``Deep reinforcement learning meets graph neural networks: Exploring a routing optimization use case,'' \emph{Computer Communications}, vol.~196, pp. 248--261, 2022, doi: 10.1016/j.comcom.2022.09.029.

\bibitem[Chen et al.(2020)]{chen2020rlrouting}
Chen, Y.-R., Rezapour, A., Tzeng, W.-G., and Tsai, S.-C. (2020). ``RL-Routing: An SDN Routing Algorithm Based on Deep Reinforcement Learning,'' \emph{IEEE Transactions on Network Science and Engineering}, vol.~7, no.~4, pp. 3110--3122, doi: 10.1109/TNSE.2020.3017502.

\bibitem[Demichelis and Chimento(2002)]{rfc3393}
Demichelis, C. and Chimento, P. (2002). \emph{{IP Packet Delay Variation Metric for IP Performance Metrics (IPPM)}}, IETF RFC 3393, Nov. 2002.

\bibitem[Dijkstra(1959)]{dijkstra1959note}
Dijkstra, E. W. (1959). ``A note on two problems in connexion with graphs,'' \emph{Numerische Mathematik}, vol.~1, no.~1, pp. 269--271.

\bibitem[Ferriol-Galm\'{e}s et al.(2023)]{almasan2022routenet}
Ferriol-Galm\'{e}s, M., Paillisse, J., Su\'{a}rez-Varela, J., Rusek, K., Xiao, S., Shi, X., Cheng, X., Barlet-Ros, P., and Cabellos-Aparicio, A. (2023). ``RouteNet-Fermi: Network modeling with graph neural networks,'' \emph{IEEE/ACM Transactions on Networking}, vol.~31, no.~6, pp. 3080--3095, doi: 10.1109/TNET.2023.3269983.

\bibitem[Hong et al.(2013)]{hong2013achieving}
Hong, C.-Y., Kandula, S., Mahajan, R., Zhang, M., Gill, V., Nanduri, M., and Wattenhofer, R. (2013). ``Achieving high utilization with software-driven WAN,'' \emph{ACM SIGCOMM Computer Communication Review}, vol.~43, no.~4, pp. 15--26.

\bibitem[Jain et al.(1984)]{jain1984quantitative}
Jain, R., Chiu, D.-M., and Hawe, W. R. (1984). ``A quantitative measure of fairness and discrimination for resource allocation in shared computer systems,'' Digital Equipment Corporation, Research Report TR-301.

\bibitem[Jain et al.(2013)]{jain2013b4}
Jain, S., Kumar, A., Mandal, S., Ong, J., Poutievski, L., Singh, A., Venkata, S., Wanderer, J., Zhou, J., Zhu, M., \emph{et al.} (2013). ``B4: Experience with a globally-deployed software defined wan,'' \emph{ACM SIGCOMM Computer Communication Review}, vol.~43, no.~4, pp. 3--14.

\bibitem[McKeown et al.(2008)]{mckeown2008openflow}
McKeown, N., Anderson, T., Balakrishnan, H., Parulkar, G., Peterson, L., Rexford, J., Shenker, S., and Turner, J. (2008). ``OpenFlow: Enabling innovation in campus networks,'' \emph{ACM SIGCOMM Computer Communication Review}, vol.~38, no.~2, pp. 69--74, doi: 10.1145/1355734.1355746.

\bibitem[Mnih et al.(2015)]{mnih2015human}
Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A.~A., Veness, J., Bellemare, M.~G., Graves, A., Riedmiller, M., Fidjeland, A.~K., Ostrovski, G., \emph{et al.} (2015). ``Human-level control through deep reinforcement learning,'' \emph{Nature}, vol.~518, no.~7540, pp. 529--533, doi: 10.1038/nature14236.

\bibitem[Moy(1998)]{moy1998ospf}
Moy, J. (1998). \emph{{OSPF Version 2}}, IETF RFC 2328, Apr. 1998.

\bibitem[Open Networking Foundation(2012)]{onf2012openflow}
{Open Networking Foundation} (2012). \emph{{OpenFlow Switch Specification Version 1.3.0}}, ONF TS-006, Jun. 2012.

\bibitem[Schaul et al.(2016)]{schaul2016prioritized}
Schaul, T., Quan, J., Antonoglou, I., and Silver, D. (2016). ``Prioritized experience replay,'' in \emph{International Conference on Learning Representations (ICLR)}.

\bibitem[Stampa et al.(2017)]{stampa2017deep}
Stampa, G., Arias, M., S\'{a}nchez-Charles, D., Munt\'{e}s-Mulero, V., and Cabellos, A. (2017). ``A deep-reinforcement learning approach for software-defined networking routing optimization,'' in \emph{Proceedings of the 13th ACM International Conference on Emerging Networking Experiments and Technologies (CoNEXT)}, pp. 48--49, 2017.

\bibitem[Sutton and Barto(2018)]{sutton2018reinforcement}
Sutton, R. S. and Barto, A. G. (2018). \emph{Reinforcement Learning: An Introduction}, 2nd~ed.\hskip 1em plus 0.5em minus 0.4em\relax MIT Press.

\bibitem[Van Hasselt et al.(2016)]{vanhasselt2016deep}
Van~Hasselt, H., Guez, A., and Silver, D. (2016). ``Deep reinforcement learning with double Q-learning,'' in \emph{Proceedings of the AAAI Conference on Artificial Intelligence}, vol.~30, no.~1, pp. 2094--2100.

\bibitem[Wang et al.(2016)]{wang2016dueling}
Wang, Z., Schaul, T., Hessel, M., Hasselt, H., Lanctot, M., and Freitas, N. (2016). ``Dueling network architectures for deep reinforcement learning,'' in \emph{International Conference on Machine Learning (ICML)}, pp. 1995--2003.

\bibitem[Yen(1971)]{yen1971finding}
Yen, J. Y. (1971). ``Finding the {$K$} shortest loopless paths in a network,'' \emph{Management Science}, vol.~17, no.~11, pp. 712--716.

\end{thebibliography}

\clearpage

% ============================================================================
% APPENDICES
% ============================================================================
\appendix

\chapter{Mathematical Formulations and Proofs}
\label{app:math_proofs}

\section{Identifiability of the Dueling Architecture}
In the Dueling Q-network, unconstrained addition $Q(s, a) = V(s) + A(s, a)$ suffers from identifiability issues: given $Q(s, a)$, one cannot uniquely recover $V(s)$ and $A(s, a)$, as adding an arbitrary scalar constant $c$ to $V(s)$ while subtracting $c$ from all $A(s, a)$ leaves $Q(s, a)$ completely unchanged.

To define a centered advantage representation, Wang et al. \cite{wang2016dueling} force the advantage function estimator to have zero mean across all actions, parameterizing the value stream by $\beta$ and the advantage stream by $\alpha$ alongside shared feature weights $\theta$:
\begin{equation}
Q(s, a; \theta, \alpha, \beta) = V(s; \theta, \beta) + \left( A(s, a; \theta, \alpha) - \frac{1}{|\mathcal{A}|} \sum_{a' \in \mathcal{A}} A(s, a'; \theta, \alpha) \right).
\end{equation}
\begin{proof}
Let $\tilde{A}(s, a) = A(s, a) - \frac{1}{|\mathcal{A}|} \sum_{a'} A(s, a')$. Summing over all $a \in \mathcal{A}$:
\begin{align}
\sum_{a \in \mathcal{A}} \tilde{A}(s, a) &= \sum_{a \in \mathcal{A}} A(s, a) - \sum_{a \in \mathcal{A}} \left( \frac{1}{|\mathcal{A}|} \sum_{a'} A(s, a') \right) \notag \\
&= \sum_{a \in \mathcal{A}} A(s, a) - |\mathcal{A}| \cdot \frac{1}{|\mathcal{A}|} \sum_{a'} A(s, a') = 0.
\end{align}
Therefore, $\frac{1}{|\mathcal{A}|} \sum_{a \in \mathcal{A}} Q(s, a) = V(s) + 0 = V(s)$. Thus, $V(s)$ equals the mean of the represented Q-values and the centered advantage is uniquely determined. Raw advantage logits can still share an arbitrary common offset, so this does not prove uniqueness of network parameters.
\end{proof}

\chapter{OpenFlow 1.3 Flow Table, Group Table, and REST API Specifications}
\label{app:openflow_api}

\section{OpenFlow 1.3 Instruction Pipeline Architecture}
In OpenFlow 1.3 (ONF TS-025 \S5.1), packet processing follows an explicit instruction pipeline rather than the legacy OpenFlow 1.0 action set:
\begin{itemize}
    \item \textbf{Instruction Sets vs. Action Sets:} An OpenFlow 1.3 flow entry contains an \emph{Instruction Set}. The instruction \code{OFPIT_APPLY_ACTIONS} applies its specified action list immediately to the packet without modifying the cumulative Action Set. In contrast, \code{OFPIT_WRITE_ACTIONS} merges actions into the switch's persistent Action Set for deferred execution upon pipeline termination. The EC499 prototype deploys single-table matching (Table 0) with \code{OFPIT_APPLY_ACTIONS} to execute \code{OFPAT_OUTPUT} immediately, avoiding pipeline state overhead.
    \item \textbf{Multipart Statistics Mechanics:} OpenFlow 1.3 consolidates all asynchronous telemetry queries into unified Multipart Requests (\code{OFPT_MULTIPART_REQUEST = 18}) and Multipart Replies (\code{OFPT_MULTIPART_REPLY = 19}). Port counter polling utilizes multipart type \code{OFPMP_PORT_STATS} (Type 4), and flow rule inspection uses \code{OFPMP_FLOW_STATS} (Type 1), replacing the discrete messages of OpenFlow 1.0.
    \item \textbf{Barrier Synchronization:} To guarantee that downstream Open vSwitch instances complete flow rule and group table installations before upstream switches inject traffic, the controller issues an explicit \code{OFPT_BARRIER_REQUEST} (Type 20) following multi-hop path installation. The switch commits all preceding messages before returning \code{OFPT_BARRIER_REPLY} (Type 21), preventing transient forwarding blackholes.
\end{itemize}

\section{OpenFlow 1.3 Flow Table Entry Structure}
Table~\ref{tab:flow_table_spec} defines the exact fields programmed into Open vSwitch software Flow Table 0 for ordinary IPv4 path rules.

\begin{table}[htbp]
\centering
\caption{OpenFlow 1.3 Flow Table Entry Field Specifications}
\label{tab:flow_table_spec}
\footnotesize
\begin{tabularx}{\textwidth}{l l X}
\toprule
\textbf{Flow Field} & \textbf{Configured Value} & \textbf{Physical Meaning / Action} \\
\midrule
\code{table_id} & $0$ & Primary ingress processing table \\
\code{priority} & $10$ or $20$ & Dynamic traffic steering rule priority \\
\code{match.eth_type} & \code{0x0800} & IPv4 unicast traffic filter \\
\code{match.ipv4_src} & Ingress Host IP & Source network host identifier \\
\code{match.ipv4_dst} & Egress Host IP & Destination network host identifier \\
\code{match.ip_proto} & Not set in the ordinary rule & Source/destination IPv4 rules can match multiple transport protocols \\
\code{instructions} & \code{OFPIT_APPLY_ACTIONS} & Immediately execute specified actions without mutating Action Set \\
\code{actions} & \code{OFPAT_OUTPUT:port_no} & Forward packet out designated switch egress port \\
\code{idle_timeout} & Configurable & Mice/elephant defaults: 60/180~s; same-switch shortcut: 30~s \\
\code{hard_timeout} & $120$ seconds & Ordinary path-rule lifetime default \\
\bottomrule
\end{tabularx}
\end{table}

\section{OpenFlow 1.3 Group Table Specifications}
Table~\ref{tab:group_table_spec} specifies the exact OpenFlow 1.3 Group Table structures implemented in \code{controller/routing_module.py} for data-plane fast failover and WCMP load balancing.

\begin{table}[htbp]
\centering
\caption{OpenFlow 1.3 Group Table Field Specifications Implemented in the Prototype}
\label{tab:group_table_spec}
\footnotesize
\begin{tabularx}{\textwidth}{l l l X}
\toprule
\textbf{Group Field} & \textbf{FF Group (\S5.6.1)} & \textbf{Select Group (\S5.6.1)} & \textbf{Operational Semantics} \\
\midrule
\code{group_id} & $600$ & $500$ & 32-bit unique group identifier on switch datapath \\
\code{type} & \code{OFPGT_FF} & \code{OFPGT_SELECT} & Fast Failover vs. Weighted Multipath selection \\
\code{bucket.weight} & Unused ($0$) & $1 \le W(p) \le 100$ & Proportional flow distribution weight from WCMP Softmax \\
\code{bucket.watch_port} & Egress port number & \code{OFPP_ANY} & Hardware link liveness monitoring port for instantaneous shift \\
\code{bucket.watch_group} & \code{OFPG_ANY} & \code{OFPG_ANY} & Secondary group chaining monitor \\
\code{bucket.actions} & \code{OFPAT_OUTPUT:port} & \code{OFPAT_OUTPUT:port} & Datapath forwarding action applied to selected bucket \\
\bottomrule
\end{tabularx}
\end{table}

\section{REST API Endpoints}
The controller exposes the following operational HTTP REST API endpoints:
\begin{itemize}
  \item \code{GET /api/health}: Returns controller health.
  \item \code{GET /api/topology}: Returns graph and link information.
  \item \code{GET /api/metrics}: Returns a bundled telemetry response.
  \item \code{GET /api/ha/status}: Returns pool health and failover history.
  \item \code{POST /api/simulate/apply_flow}: Injects a software-model flow.
  \item \code{POST /api/simulate/link_fail}: Changes a simulated link state.
\end{itemize}

\chapter{Automated Test Suite Verification Listing}
\label{app:test_suite}
The delivery test suite contains the following 42 unit and integration checks. Execution time is environment-dependent; a passing run validates only the behaviours covered by these tests:
\begin{enumerate}
  \item \code{test_agent_and_state_manager_with_config_defaults}
  \item \code{test_config_dictionary_structure}
  \item \code{test_env_var_override_and_type_casting}
  \item \code{test_ha_config_presence}
  \item \code{test_closed_loop_flow_accumulation_and_expiration}
  \item \code{test_generalized_core_congestion_across_topologies}
  \item \code{test_polyak_soft_update_consistency}
  \item \code{test_seeded_workloads_are_reproducible_and_distinct}
  \item \code{test_dqn_router_lifecycle}
  \item \code{test_dueling_architecture}
  \item \code{test_controller_node_properties}
  \item \code{test_ha_pool_cascaded_failovers}
  \item \code{test_ha_pool_init_and_active_leader}
  \item \code{test_ha_pool_ovs_targets_format}
  \item \code{test_all_topologies}
  \item \code{test_random_topology_generation}
  \item \code{test_replay_buffer_sampling}
  \item \code{test_sumtree_arithmetic}
  \item \code{test_configurable_state_dimension_and_no_fake_route}
  \item \code{test_control_overhead_accounting}
  \item \code{test_differential_port_rates}
  \item \code{test_directional_dynamic_flow_accounting_and_release}
  \item \code{test_flow_table_records}
  \item \code{test_host_location_tracking}
  \item \code{test_inject_traffic_flow_duration_and_latency_scaling}
  \item \code{test_jitter_calculation}
  \item \code{test_link_failure_and_restoration}
  \item \code{test_network_te_summary}
  \item \code{test_packet_loss_modeling}
  \item \code{test_routing_state_features}
  \item \code{test_compute_path_metrics}
  \item \code{test_dijkstra_spf}
  \item \code{test_ecmp_routing}
  \item \code{test_ospf_routing}
  \item \code{test_wsp_and_llr_routing}
  \item \code{test_dashboard_model_telemetry}
  \item \code{test_ha_status_endpoint}
  \item \code{test_model_inspect_and_predict}
  \item \code{test_mutations_require_post_and_flow_is_counted_once}
  \item \code{test_versus_endpoint_all_baselines}
  \item \code{test_versus_endpoint_multi_protocol_checklist}
  \item \code{test_versus_endpoint_single_protocol}
\end{enumerate}

\chapter{Supporting Implementation Notes}
\label{app:viva_voce}

This appendix records implementation details that support the project description without interrupting the main account.

\section{Candidate Paths and Input Features}
The input vector always contains ten summary features, even when graph size changes. Unavailable candidate positions are padded, and selection is restricted to the available candidate count. The benefit is a fixed neural interface. The limitation is that different graph and traffic states can produce similar summaries. Candidate ordering and tie-breaking can also affect which action index represents a path.

\section{Replay Priorities and Storage}
The SumTree stores cumulative priorities in \code{float32}. A priority update propagates a difference through the ancestors of the corresponding leaf. The current implementation has no periodic full-tree rebuild, so long-run round-off behaviour remains a numerical issue to test.

The buffer also stores state, action, reward, next-state, and terminal arrays, with compatibility tuples. Its memory use cannot be determined from the tree array alone. Capacity is configurable through \code{RL_MEMORY_SIZE}; the current default is 5,000 transitions.

\section{Queue-Model Limits}
The model represents a finite queue and allows offered utilisation above one. The numerical queue-delay cap bounds a reported software value, not physical waiting time. Likewise, the quadratic congestion term encourages lower-load routes but does not establish capacity feasibility. Bursty packet arrivals can differ from the model assumptions.

\section{Meaning of the Recovery Measurements}
A pool member is selected through local state and health probing. The 0.001~ms observation refers to local bookkeeping; the 37.96~ms observation refers to client HTTP recovery in the reported test. They do not measure distributed agreement, consistent state recovery, or OpenFlow reconnection. Existing OVS entries may continue forwarding while valid, but packet continuity was not instrumented across the failure.

\section{Supporting Files}
The delivery contains the controller, routing, agent, topology, and test source; the model checkpoint; the final model-result artifacts; and the packet run \code{mininet_20261026T173329Z_seed2026}. The packet bundle includes environment information, trial conditions, raw measurements, summaries, and analysis JSON. These files provide the basis for checking the reported tables.

\chapter{User \& Administrator Deployment Manual and Operational Runbook}
\label{app:manual}

\section{System Prerequisites and Dependencies}
The Adaptive SDN Traffic Engineering Platform is engineered to run natively on Linux-based environments (Ubuntu 20.04 LTS, Ubuntu 22.04 LTS, Ubuntu 24.04 LTS, or Debian 11/12).

\subsection{Hardware Requirements \& Reference Deployment Environment}
The reference experimental setup was hosted inside a dedicated 64-bit Ubuntu virtual machine running under the VMware hypervisor (see Figure~\ref{fig:vmware_specs}):
\begin{itemize}
    \item \textbf{Virtual Processors}: 4 virtual CPU cores (vCPUs) with hardware virtualization extensions enabled.
    \item \textbf{System Memory (RAM)}: 8.0~GB of dedicated memory (minimum: 4~GB; 8~GB recommended for 20-switch Clos emulations).
    \item \textbf{Disk Storage}: 60.0~GB SCSI virtual disk (minimum: 10~GB free space for dependencies, dataset logs, and model checkpoints).
    \item \textbf{Network Adapter}: NAT virtual adapter with isolated internal loopback for OpenFlow and REST dashboard communication.
\end{itemize}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.72\textwidth]{vmware_virtual_machine_specs.png}
\caption{VMware Virtual Machine Hardware Configuration for the Experimental Platform (Ubuntu 64-bit, 4 vCPUs, 8~GB RAM, 60~GB SCSI Storage).}
\label{fig:vmware_specs}
\end{figure}

\subsection{Software Requirements}
\begin{itemize}
    \item \textbf{Operating System}: Linux kernel 5.4 or higher (the empirical benchmark testbed was evaluated on Ubuntu Linux kernel 7.0.0-31) with Open vSwitch kernel module support.
    \item \textbf{Python Environment}: Separate environments: the packet runner uses Python 3.14.4 (active Spring 2026 Ubuntu environment); the legacy Ryu/Eventlet controller uses Python 3.10. Ryu compatibility should be checked in the controller interpreter.
    \item \textbf{Network Virtualization}: Mininet Version 2.3.0+ and Open vSwitch (OVS) 2.13+.
    \item \textbf{Deep Learning Framework}: PyTorch 2.0+ (CPU or CUDA).
    \item \textbf{SDN Framework}: Ryu SDN Framework 4.34+.
    \item \textbf{Web Browser}: Google Chrome, Chromium, Firefox, or Safari with HTML5 Canvas support.
\end{itemize}

\section{Installation and Environment Initialization}
The launchers select interpreters by dependency requirements. A clean installation must provision the scientific environment and the separate Ryu controller environment.

\subsection{Step-by-Step Installation}
\begin{lstlisting}[language=bash, caption={Platform Environment Setup}]
# From the extracted delivery bundle
cd 03_Source

# Scientific environment
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Separate legacy controller environment
python3.10 -m venv .venv-controller
.venv-controller/bin/python -m pip install -r requirements.txt
\end{lstlisting}

\section{Automated Execution Runbook}

\subsection{1. Execute Unit \& Integration Tests (42 Tests)}
To assert software integrity across all 42 automated unit and integration tests:
\begin{lstlisting}[language=bash]
./EC499tests/run_tests.sh
\end{lstlisting}

\subsection{2. Execute the Head-to-Head Tournament Benchmark}
To run the automated routing tournament across all 5 topologies:
\begin{lstlisting}[language=bash]
./EC499tests/run_benchmarks.sh
\end{lstlisting}
Benchmark results are written to \texttt{logs/routing\_tournament\_results.json}.

\subsection{3. Execute Multi-Topology Stress Testing}
To evaluate severe core link saturation, flow avalanches, and link failures:
\begin{lstlisting}[language=bash]
./.venv/bin/python EC499tests/stress_test_blind_topologies.py
\end{lstlisting}

\subsection{4. Evaluate Zero-Shot Random Graph Generalization}
To test the pre-trained model on arbitrary unseen random graphs:
\begin{lstlisting}[language=bash]
./EC499tests/run_random_blind_test.sh --nodes 25 --flows 200
\end{lstlisting}

\subsection{5. Launch the Prototype (Controller + Web Dashboard)}
To start the Ryu SDN controller alongside the interactive Web Dashboard:
\begin{lstlisting}[language=bash]
chmod +x run_system.sh
./run_system.sh
\end{lstlisting}
Open a modern web browser to access the interactive HTML5 canvas dashboard:
\begin{equation*}
    \texttt{http://localhost:8080}
\end{equation*}

\subsection{6. Standalone Web Dashboard Launcher}
The Web Dashboard can also be launched independently for testing and visualization:
\begin{lstlisting}[language=bash]
python3 controller/web_dashboard.py --port 8080 --topo tree
\end{lstlisting}

\section{Interactive Web Dashboard User Guide}
The Web Dashboard interface is structured into six functional zones:
\begin{enumerate}
    \item \textbf{Global Navigation Bar}:
    \begin{itemize}
        \item \textit{Fabric Topology Pill}: Displays the active network topology (e.g., Hierarchical Tree, Clos Fat-Tree).
        \item \textit{Model Parameters Badge}: Displays loaded D3QN weights ($26,501$ parameters). Clicking opens the Neural Network Inspector modal.
        \item \textit{Exploration Badge ($\varepsilon$)}: Shows the active exploration rate ($\varepsilon = 0.010$).
        \item \textit{Theme Toggle (Light/Dark)}: Instantly toggles between high-contrast daylight theme and dark mode.
        \item \textit{Telemetry Auto-Refresh}: Pauses or activates automatic 2.5-second telemetry polling.
        \item \textit{Network Settings Button}: Opens the global architecture configuration modal.
    \end{itemize}
    
    \item \textbf{Real-Time KPI Strip}:
    \begin{itemize}
        \item \textit{Fabric Throughput (Mbps)}: Real-time aggregated data plane throughput with active flow count.
        \item \textit{Bottleneck Load (\%)}: Peak link utilization across all network links with status pill (Optimal $<45\%$, Moderate $45$--$75\%$, Congested $>75\%$).
        \item \textit{Latency \& Jitter (ms)}: Average end-to-end path latency, Echo-RTT delay variation, and packet loss percentage.
        \item \textit{Control Plane Rate (msg/s)}: OpenFlow asynchronous message throughput and mean D3QN decision latency.
    \end{itemize}
    
    \item \textbf{Interactive OpenFlow 1.3 Canvas Fabric}:
    \begin{itemize}
        \item \textit{Pan \& Zoom Controls}: Zoom In ($+$), Zoom Out ($-$), Reset Zoom ($100\%$), or use mouse wheel zoom centered at cursor position.
        \item \textit{Node Selection}: Click any switch node to designate it as the Source switch (green halo) or Destination switch (pink halo).
        \item \textit{Utilization Badges}: Real-time link percentage badges displaying link saturation levels.
        \item \textit{Severed Link Overlay}: Rendered as dashed red lines with a central \texttt{[SEVERED]} badge during simulated link failures.
    \end{itemize}
    
    \item \textbf{Interactive Route Predictor \& Decision Explainer}:
    \begin{itemize}
        \item \textit{Source \& Destination Selectors}: Dropdowns allowing instant selection of ingress and egress edge switches.
        \item \textit{Demand Slider}: Adjusts simulated flow bandwidth demand between 5~Mbps and 95~Mbps.
        \item \textit{Predict Route Button}: Dispatches an asynchronous request to \code{/api/model_predict}, executing D3QN inference ($<2.5\text{ ms}$).
        \item \textit{Apply Flow to Fabric Button}: Dynamically injects the selected flow into the active state manager, updating link loads and flow tables in real-time.
        \item \textit{Softmax Q-Value Table}: Renders all candidate path alternatives, action indices $a^*$, Q-softmax choice probabilities, projected bottlenecks, and path latencies.
    \end{itemize}
    
    \item \textbf{Algorithm Tournament Arena}:
    \begin{itemize}
        \item \textit{Protocol Checklist Chips}: Toggle D3QN, OSPF, ECMP, WSP, LLR, or Dijkstra SPF for comparative head-to-head simulation.
        \item \textit{Workload Pattern}: Select between Poisson, Core Congestion Jamming, or Asymmetric Burst Shockwave.
        \item \textit{Plot View Tabs}: Switch seamlessly between All-in-One Triad, Metric Deltas (Bar), Delay Trajectory (Timeline), 6D Quality Radar, Latency CDF (Tail SLA), and Load Scaling Curves.
    \end{itemize}
    
    \item \textbf{Fault Injection and Anomaly Emulation Toolbar}:
    \begin{itemize}
        \item \textit{Sever Link}: Simulates a physical fiber cut on a candidate core or aggregation trunk link.
        \item \textit{Synthetic Link Degradation Mode}: Degrades link capacity by 90\% with an artificial latency penalty.
        \item \textit{Transient Traffic Surge Injection (+50 Mbps)}: Injects an instant +50~Mbps traffic surge to stress the active routing path.
        \item \textit{Restore Links}: Restores all severed or degraded links to nominal operating status.
        \item \textit{Flush Flows}: Flushes all dynamic flow table entries to baseline idle state.
    \end{itemize}
\end{enumerate}

\section{REST API Specification \& Endpoint Reference}
The embedded HTTP server exposes a complete RESTful API for external monitoring, telemetry polling, and automation scripting. The endpoints are divided into telemetry/diagnostic interfaces and active flow/simulation interfaces:

\begin{table}[H]
\centering
\caption{REST API Reference: Telemetry, Diagnostics, and Model Inference Endpoints}
\label{tab:rest_api_telemetry}
\small
\begin{tabularx}{\textwidth}{l l p{3.0cm} X}
\toprule
\textbf{Method} & \textbf{Endpoint} & \textbf{Parameters} & \textbf{Description \& Output Schema} \\
\midrule
\texttt{GET} & \code{/api/health} & None & Returns controller health, active topology ID, switch count, link count, and active flow count. \\
\addlinespace
\texttt{GET} & \code{/api/telemetry} & \texttt{topo=\{id\}} & Fast single round-trip bundle containing topology layout, network TE stats, control overhead, RL metrics, and active flows. \\
\addlinespace
\texttt{GET} & \code{/api/topology} & \texttt{topo=\{id\}} & Returns graph nodes with 2D positions ($x, y$), switch types, link capacities, delays, and current utilization. \\
\addlinespace
\texttt{GET} & \code{/api/stats} & None & Returns network-wide aggregated TE summary (throughput, mean utilization, bottleneck load, latency, jitter, loss). \\
\addlinespace
\texttt{GET} & \code{/api/control_overhead} & None & Returns OpenFlow message generation rates (msg/s) and mean D3QN decision latency (ms). \\
\addlinespace
\texttt{GET} & \code{/api/rl_metrics} & None & Returns exploration rate $\varepsilon$, model device, parameter count, and buffer capacity. \\
\addlinespace
\texttt{GET} & \code{/api/model_inspect} & None & Detailed PyTorch neural architecture inspection including layer dimensions, parameter count, and tensor shapes. \\
\addlinespace
\texttt{GET} & \code{/api/model_predict} & \texttt{src}, \texttt{dst}, \texttt{demand} & Real-time forward inference returning chosen path, candidate path alternatives, action indices, and softmax probabilities. \\
\bottomrule
\end{tabularx}
\end{table}

\begin{table}[H]
\centering
\caption{REST API Reference: Dynamic Control, Traffic Injection, and Simulation Endpoints}
\label{tab:rest_api_control}
\small
\begin{tabularx}{\textwidth}{l l p{3.0cm} X}
\toprule
\textbf{Method} & \textbf{Endpoint} & \textbf{Parameters} & \textbf{Description \& Output Schema} \\
\midrule
\texttt{GET/POST} & \code{/api/versus} & \texttt{topo}, \texttt{protocols}, \texttt{pattern}, \texttt{flows} & Head-to-head algorithm tournament simulation returning comparative metrics, trajectories, and Pareto efficiency verdicts. \\
\addlinespace
\texttt{GET} & \code{/api/flows} & None & Returns active flow table entries (flow ID, DPID, match criteria, actions, byte counters, duration). \\
\addlinespace
\texttt{POST} & \code{/api/simulate/apply_flow} & \texttt{src}, \texttt{dst}, \texttt{demand} & Injects a dynamic flow into the network state manager and updates port counters. \\
\addlinespace
\texttt{POST} & \code{/api/simulate/traffic_burst} & None & Injects an asymmetric +50~Mbps surge across the core trunks. \\
\addlinespace
\texttt{POST} & \code{/api/simulate/core_jamming} & None & Injects severe core link congestion ($96\%$ saturation) to trigger autonomous rerouting. \\
\addlinespace
\texttt{POST} & \code{/api/network_settings} & JSON payload & Configures queue depths ($K$), link bandwidths, propagation delays, and physical packet drop rates. \\
\addlinespace
\texttt{GET} & \code{/api/plots/\{filename\}} & None & Serves static high-resolution benchmark and telemetry plots as PNG images. \\
\bottomrule
\end{tabularx}
\end{table}

\section{Mininet CLI Operations and OVS Diagnostics}
When running interactive emulations, the Mininet command-line interface provides real-time control:

\begin{lstlisting}[language=bash, caption={Interactive Mininet CLI Emulation Workflow}]
# Launch Mininet with Fat-Tree Clos topology
sudo /usr/bin/python3 topology/mininet_topo.py --topo fattree --controller-port 6633 --no-traffic

# Inside the Mininet CLI:
mininet> pingall             # Verify full Layer 2 and Layer 3 reachability
mininet> h1 ping -c 5 h16    # Measure end-to-end ping RTT across pod boundaries
mininet> iperf h1 h16        # Generate TCP bandwidth stream between edge hosts
mininet> link s1 s5 down     # Simulate physical link failure between core and agg
\end{lstlisting}

\subsection{Reproducible Packet-Level Mininet Experiment}
\label{app:mininet_protocol}
The scripted experiment is preferred to ad-hoc CLI measurements because it records randomized condition order, raw command output, code hashes, and environment versions. It must be run on a Linux host with Mininet, Open vSwitch, iperf (version 2), and the controller virtual environment installed. It requires root privileges for network namespaces:
\begin{lstlisting}[language=bash, caption={Executing the 120-Trial Factorial Packet Experiment}]
cd EC499tests
sudo ./run_mininet_experiment.sh --matrix --replicates 10
./run_mininet_analysis.sh
\end{lstlisting}
The first command produces 120 randomized trials (2 topologies $\times$ 3 policies $\times$ 2 protocols $\times$ 10 replicates) and writes every raw artifact under \code{logs/mininet\_trials/}. The second command creates summary statistics and a figure only if successful measured trials exist; it deliberately fails rather than fabricate absent data. Before citing a packet-level result, preserve the raw run directory, \code{mininet\_measured\_trials.json}, \code{mininet\_measured\_analysis.json}, and the generated figure in the submission archive.

\subsection{OpenFlow Flow Table Inspection via Open vSwitch}
To inspect live OpenFlow 1.3 flow tables and port statistics from the Linux shell:
\begin{lstlisting}[language=bash, caption={Open vSwitch Flow Table Diagnostics}]
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-ofctl -O OpenFlow13 dump-groups s1
sudo ovs-ofctl -O OpenFlow13 dump-ports-desc s1
sudo ovs-ofctl -O OpenFlow13 dump-ports s1
\end{lstlisting}

\section{Pareto Sensitivity Ablation and Dynamic Telemetry Tuning}
The platform provides automated ablation tooling to evaluate the trade-offs of the multi-objective reward formulation:

\begin{lstlisting}[language=bash, caption={Executing the Pareto Sensitivity Ablation Suite}]
# Execute 50-episode sweep across 6 SLA weight configurations:
./.venv/bin/python EC499tests/ablate_reward_weights.py

# Expected outputs:
# - logs/pareto_sensitivity_ablation.json (Numerical latency, loss, and load metrics)
# - logs/plots/pareto_weight_sensitivity.png (Publication-grade 4-panel figure)
\end{lstlisting}

\subsection{Configuring Shadow Reservations and TCAM Allocation}
Operators can tune active shadow reservation parameters and TCAM allocation timeouts directly in \texttt{config.py} or via the corresponding environment variables:
\begin{itemize}
    \item \code{SDN_SHADOW_DECAY_HALF_LIFE}: Half-life decay duration in seconds (default: $1.5\text{ s}$). Controls how fast temporary flow reservations decay between OpenFlow telemetry polling cycles.
    \item \code{ELEPHANT_FLOW_THRESHOLD_MBPS}: Rate threshold for elephant flow classification (default: $5.0\text{ Mbps}$). Observed rate selects the elephant priority/timeout class; ordinary IPv4 rules match source and destination IP addresses.
    \item \code{SDN_FLOW_IDLE_TIMEOUT_MICE}: Idle timeout for wildcard aggregated mice flows (default: $60\text{ s}$).
    \item \code{SDN_FLOW_IDLE_TIMEOUT_ELEPHANT}: Idle timeout for pinned elephant flows (default: $180\text{ s}$).
\end{itemize}

\clearpage
\subsection{Operational Troubleshooting and Recovery Runbook}
Table~\ref{tab:troubleshooting_guide} provides network operators with a rapid diagnostic and remediation matrix for common runtime anomalies encountered in production software-defined fabrics:

\begin{table}[H]
\centering
\caption{Operational Troubleshooting and Anomaly Remediation Runbook}
\label{tab:troubleshooting_guide}
\small
\begin{tabularx}{\textwidth}{p{2.8cm} p{2.8cm} p{3.8cm} X}
\toprule
\textbf{Symptom} & \textbf{Probable Cause} & \textbf{Diagnostic Command} & \textbf{Remediation Procedure} \\
\midrule
OpenFlow socket timeout & Controller not bound to 6633 or firewall drop & \texttt{netstat -tuln |} \newline \texttt{grep 6633} & Launch controller via \texttt{./run\_system.sh} and ensure iptables allows TCP 6633 loopback traffic. \\
\addlinespace
Mininet switches show \texttt{DISCONNECTED} & Controller process or connection unavailable & \texttt{curl -s localhost:} \newline \texttt{8080/api/ha/status} & Check controller process and standby health. The $0.001$~ms figure covers only local bookkeeping, not failure detection, consensus, or OpenFlow reconnection. \\
\addlinespace
D3QN inference latency $>10\text{ ms}$ & CPU thread contention or unbounded state history & \texttt{top -b -n 1 |} \newline \texttt{grep python3} & Restrict PyTorch threads (\texttt{export OMP\_NUM\_THREADS=4}); clear stale trajectory queues. \\
\addlinespace
TCAM table space saturation warning & Excessive elephant flow rules pinned without expiry & \texttt{sudo ovs-ofctl} \newline \texttt{dump-flows s1 | wc -l} & Issue REST POST to \code{/api/simulate/clear_flows} or decrease \code{SDN_FLOW_IDLE_TIMEOUT_MICE} to 5s. \\
\bottomrule
\end{tabularx}
\end{table}

\end{document}
'''
```
