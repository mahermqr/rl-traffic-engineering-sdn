# Chapter 4: The Proposed System (Part 1 - Design and Experiments)

CHAPTER_4_DESIGN_EXP = r'''% ============================================================================
% CHAPTER 4: THE PROPOSED SYSTEM (DESIGN, EXPERIMENTS, EVALUATION, RESULTS)
% ============================================================================
\chapter{The Proposed System}
\label{chap:project}

In accordance with the Faculty of Engineering graduation project curriculum, this chapter presents the complete engineering lifecycle of the proposed platform across four rigorous sections: \textbf{Design} (Section~\ref{sec:design}), \textbf{Experiments} (Section~\ref{sec:experiments}), \textbf{Testing \& Evaluation} (Section~\ref{sec:testing}), and \textbf{Results and Discussion} (Section~\ref{sec:results}).

% ----------------------------------------------------------------------------
% 4.1 DESIGN
% ----------------------------------------------------------------------------
\section{Design}
\label{sec:design}

\subsection{Top-Level Closed-Loop Control Architecture}
The proposed platform operates as an autonomous closed-loop control system structured across three functional planes: the \textbf{Data Plane}, the \textbf{Control Plane}, and the \textbf{Intelligence Plane}. Figure~\ref{fig:closed_loop_arch} illustrates the top-level architectural layout and the continuous interaction cycle.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.88, every node/.style={transform shape},
    planebox/.style={draw=gray!30, fill=gray!4, rounded corners=6pt, dashed},
    swbox/.style={draw=orange!80!black, fill=orange!12, rounded corners=4pt, thick, align=center, minimum width=2.1cm, minimum height=0.95cm, font=\scriptsize\bfseries},
    ctrlbox/.style={draw=blue!80!black, fill=blue!12, rounded corners=4pt, thick, align=center, minimum width=2.1cm, minimum height=0.95cm, font=\scriptsize\bfseries},
    drlbox/.style={draw=teal!80!black, fill=teal!12, rounded corners=4pt, thick, align=center, minimum width=2.1cm, minimum height=0.95cm, font=\scriptsize\bfseries},
    lbl/.style={font=\footnotesize\bfseries, color=gray!70!black},
    arr/.style={->, >=Stealth, thick},
    darr/.style={<->, >=Stealth, thick}
]

% Background Planes
\draw[planebox] (-1.4, -0.75) rectangle (13.4, 0.95);
\draw[planebox] (-1.4, 1.45) rectangle (13.4, 3.15);
\draw[planebox] (-1.4, 3.65) rectangle (13.4, 5.35);

% Data Plane
\node[swbox] (sw1) at (0.0, 0.0) {OVS Switch $S_1$\\ {\tiny (LLDP Forwarding)}};
\node[swbox] (sw2) at (4.0, 0.0) {OVS Switch $S_2$\\ {\tiny (Port Counters)}};
\node[swbox] (sw3) at (8.0, 0.0) {OVS Switch $S_3$\\ {\tiny (TCAM Flow Table 0)}};
\node[swbox] (sw4) at (12.0, 0.0) {OVS Switch $S_4$\\ {\tiny (Buffer Queues)}};
\draw[thick, double, color=gray!60!black] (sw1) -- (sw2) -- (sw3) -- (sw4);
\node[lbl, anchor=west] at (-1.2, 0.72) {DATA PLANE (Infrastructure Layer / OpenFlow 1.3)};

% Control Plane
\node[ctrlbox] (c_topo) at (0.0, 2.2) {Topology Discovery\\ {\tiny (LLDP Snoop)}};
\node[ctrlbox] (c_mon)  at (4.0, 2.2) {Telemetry Collector\\ {\tiny (PortStats Poller)}};
\node[ctrlbox] (c_flow) at (8.0, 2.2) {FlowMod Dispatcher\\ {\tiny (Path Installer)}};
\node[ctrlbox] (c_ha)   at (12.0, 2.2) {HA Controller Pool\\ {\tiny (Health Probes)}};
\node[lbl, anchor=west] at (-1.2, 2.92) {CONTROL PLANE (Ryu Framework / Southbound Engine)};

% DRL Application Plane
\node[drlbox] (d_ksp)   at (0.0, 4.4) {Yen's $K$-Path Pool\\ {\tiny ($K=4$ Loopless Action)}};
\node[drlbox] (d_state) at (4.0, 4.4) {State Encoder\\ {\tiny (10D Norm Vector)}};
\node[drlbox] (d_d3qn)  at (8.0, 4.4) {D3QN Policy Net\\ {\tiny (Dueling Double DQN)}};
\node[drlbox] (d_per)   at (12.0, 4.4) {Binary SumTree PER\\ {\tiny ($O(\log N)$ Sampling)}};
\node[lbl, anchor=west] at (-1.2, 5.12) {INTELLIGENCE PLANE (Deep Reinforcement Learning Engine)};

% Collinear Orthogonal Connections
\draw[arr, color=orange!80!black] (sw1) -- node[right, font=\tiny, fill=white, inner sep=1pt] {LLDP Snoop} (c_topo);
\draw[arr, color=blue!80!black] (c_topo) -- node[right, font=\tiny, fill=white, inner sep=1pt] {Graph $G(V,E)$} (d_ksp);

\draw[arr, color=orange!80!black] (sw2) -- node[right, font=\tiny, fill=white, inner sep=1pt] {OFPPortStatsReply} (c_mon);
\draw[arr, color=teal!80!black] (c_mon) -- node[right, font=\tiny, fill=white, inner sep=1pt] {$\Delta t$ Raw Stats} (d_state);

\draw[arr, color=teal!80!black] (d_ksp) -- node[above, font=\tiny, fill=white, inner sep=1.5pt] {$K$ Candidate Paths} (d_state);
\draw[arr, color=teal!80!black] (d_state) -- node[above, font=\tiny, fill=white, inner sep=1.5pt] {State $\mathbf{s} \in \mathbb{R}^{10}$} (d_d3qn);
\draw[darr, color=purple!70!black] (d_d3qn) -- node[above, font=\tiny, fill=white, inner sep=1.5pt] {TD Error $\delta$} (d_per);

\draw[arr, color=blue!80!black] (d_d3qn) -- node[right, font=\tiny, fill=white, inner sep=1pt] {Selected Path $a^*$} (c_flow);
\draw[arr, color=blue!80!black] (c_flow) -- node[right, font=\tiny, fill=white, inner sep=1pt] {OFPFlowMod (Add/Mod)} (sw3);

\draw[darr, color=blue!80!black] (c_ha) -- node[right, font=\tiny, fill=white, inner sep=1pt] {Multi-Target OFP} (sw4);
\end{tikzpicture}
\caption{Closed-Loop SDN Control Plane and DRL Application Architecture.}
\label{fig:closed_loop_arch}
\end{figure}

The closed loop operates continuously:
\begin{enumerate}
    \item Open vSwitch (OVS) switches in the Data Plane execute packet forwarding via TCAM flow tables.
    \item The Ryu controller polls port counters every $\Delta t = 1.0$~s using \code{OFPPortStatsRequest}.
    \item First-order differentials $\Delta tx\_bytes$ are computed to derive instantaneous link load $\lambda_e(t)$ and utilization $u_e(t) = \lambda_e(t) / C_e$.
    \item The State Encoder synthesizes a normalized 10-dimensional telemetry vector $\mathbf{s}_t \in \mathbb{R}^{10}$.
    \item The PyTorch D3QN engine performs a forward inference pass ($0.24$~ms) to select the optimal loopless path $a_t^* = \arg\max_a Q(\mathbf{s}_t, a)$.
    \item The FlowMod Dispatcher generates \code{OFPFlowMod} messages instructing switches to program corresponding forwarding rules.
    \item Experiences $(\mathbf{s}_t, a_t, r_t, \mathbf{s}_{t+1}, d_t)$ are stored in the binary SumTree PER buffer for asynchronous training.
\end{enumerate}

\subsection{Continuous 10-Dimensional State Space Representation and Action Masking}
Rather than using raw unscaled counters, the agent consumes a continuous 10-dimensional state vector $\mathbf{s} \in \mathbb{R}^{10}$, normalized into the numerical range $[0.0, 1.0]$. The vector explicitly encodes topological hop distance, per-candidate bottleneck utilizations, per-candidate end-to-end latencies, and global network congestion. The exact feature layout produced by \code{controller/state_manager.py} is formalized in Table~\ref{tab:state_vector}.

\begin{table}[htbp]
\centering
\caption{Continuous 10-Dimensional Normalized State Feature Vector Layout}
\label{tab:state_vector}
\scriptsize
\begin{tabularx}{\textwidth}{c l X l}
\toprule
\textbf{Index} & \textbf{Feature Symbol} & \textbf{Physical Description} & \textbf{Normalization Mapping} \\
\midrule
$s_0$ & $\hat{H}_{\text{min}}$ & Shortest path hop count (Dijkstra SPF) & $\min(1.0, \max(0.1, \text{hops} / 10.0))$ \\
$s_1$ & $\hat{u}_0$ & Bottleneck link utilization of Candidate Path 0 & $\min(1.0, \max(0.0, \max_{e \in P_0} u_e))$ \\
$s_2$ & $\hat{u}_1$ & Bottleneck link utilization of Candidate Path 1 & $\min(1.0, \max(0.0, \max_{e \in P_1} u_e))$ \\
$s_3$ & $\hat{u}_2$ & Bottleneck link utilization of Candidate Path 2 & $\min(1.0, \max(0.0, \max_{e \in P_2} u_e))$ \\
$s_4$ & $\hat{u}_3$ & Bottleneck link utilization of Candidate Path 3 & $\min(1.0, \max(0.0, \max_{e \in P_3} u_e))$ \\
$s_5$ & $\hat{D}_0$ & Normalized end-to-end latency of Candidate Path 0 & $\min(1.0, \max(0.0, \sum_{e \in P_0} d_e / 50.0\text{ ms}))$ \\
$s_6$ & $\hat{D}_1$ & Normalized end-to-end latency of Candidate Path 1 & $\min(1.0, \max(0.0, \sum_{e \in P_1} d_e / 50.0\text{ ms}))$ \\
$s_7$ & $\hat{D}_2$ & Normalized end-to-end latency of Candidate Path 2 & $\min(1.0, \max(0.0, \sum_{e \in P_2} d_e / 50.0\text{ ms}))$ \\
$s_8$ & $\hat{D}_3$ & Normalized end-to-end latency of Candidate Path 3 & $\min(1.0, \max(0.0, \sum_{e \in P_3} d_e / 50.0\text{ ms}))$ \\
$s_9$ & $\hat{u}_{\text{peak}}$ & Network-wide peak link utilization across all edges & $\min(1.0, \max(0.0, \max_{e \in E} u_e))$ \\
\bottomrule
\end{tabularx}
\end{table}

\paragraph{Handling Variable Candidate Path Counts and Invalid Action Masking:}
When the network topology does not yield $K=4$ loopless paths between an ingress-egress pair (e.g., in sparse meshes where only two loopless paths exist), two complementary mechanisms ensure mathematical consistency:
\begin{enumerate}
    \item \textbf{Penalty Feature Padding:} For any candidate index $i \ge \text{candidate\_count}$, the state manager sets $\hat{u}_i = 1.0$ and $\hat{D}_i = 1.0$. This ensures the input tensor maintains a fixed dimension $\mathbb{R}^{10}$ while providing an immediate penalty signal to the neural network.
    \item \textbf{Dynamic Invalid-Action Masking:} In the policy network forward pass (\code{agent/dqn_router.py}), action selection is restricted to physically available candidate paths via dynamic tensor slicing:
    \begin{equation}
    a^* = \arg\max_{a \in \{0, \dots, K_{\text{avail}}-1\}} Q(\mathbf{s}, a)
    \end{equation}
    where $K_{\text{avail}} = \min(K, \text{candidate\_count})$. In exploration mode ($\epsilon$-greedy), uniform random selection is similarly constrained to $\{0, \dots, K_{\text{avail}}-1\}$. This guarantees that the agent never selects a non-existent candidate route.
\end{enumerate}

\paragraph{Fixed Summary Path Features vs. True Graph Invariance:}
This 10-dimensional state representation operates on \emph{summary path statistics} rather than raw graph adjacency matrices. This design choice enables the model to ingest paths from different topologies without changing neural network weights or tensor dimensions. However, this is distinct from true graph permutation equivariance (such as that offered by Message-Passing Graph Neural Networks); our zero-shot generalization findings represent empirical transfer over the tested graph distributions, rather than a theoretical proof of arbitrary graph invariance.

\subsection{Candidate Action Space Pruning via Yen's $K$-Shortest Paths}
To prevent combinatorial action explosion ($O(|V|^2)$), the agent's action space $\mathcal{A}$ is constrained to $K = 4$ loopless candidate paths synthesized via Yen's algorithm \cite{yen1971finding}. Figure~\ref{fig:yen_ksp} illustrates the candidate path pruning procedure.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.88, every node/.style={transform shape},
    gnode/.style={circle, draw=blue!80!black, fill=blue!15, thick, minimum size=0.9cm, font=\small\bfseries},
    rootnode/.style={circle, draw=green!70!black, fill=green!20, thick, minimum size=0.9cm, font=\small\bfseries},
    devnode/.style={circle, draw=red!80!black, fill=red!20, thick, minimum size=0.9cm, font=\small\bfseries},
    spurnode/.style={circle, draw=orange!80!black, fill=orange!20, thick, minimum size=0.9cm, font=\small\bfseries},
    path1edge/.style={line width=2.5pt, color=green!60!black, ->, >=Stealth},
    spuredge/.style={line width=2.5pt, color=orange!80!black, ->, >=Stealth, dashed},
    normedge/.style={thick, color=gray!60!black, ->, >=Stealth},
    maskededge/.style={line width=2pt, color=red!70!black, ->, >=Stealth, dotted}
]

% Graph Nodes
\node[rootnode] (S) at (0, 1.8) {$S$};
\node[devnode] (A) at (3.2, 3.5) {$v_{\text{dev}}$};
\node[gnode] (B) at (3.2, 0.1) {$B$};
\node[gnode] (C) at (6.8, 3.5) {$C$};
\node[spurnode] (E) at (6.8, 0.1) {$E$};
\node[rootnode] (D) at (10.0, 1.8) {$D$};

% Edges
\draw[path1edge] (S) -- (A);
\draw[maskededge] (A) -- (C);
\draw[path1edge] (C) -- (D);
\draw[normedge] (S) -- (B);
\draw[spuredge] (A) -- (E);
\draw[normedge] (B) -- (E);
\draw[spuredge] (E) -- (D);

% Edge Labels explicitly placed at safe midpoints
\node[font=\scriptsize\bfseries, color=green!60!black, fill=white, inner sep=1.5pt] at (1.2, 2.9) {Root Path};
\node[font=\scriptsize\bfseries, color=red!70!black, fill=white, inner sep=1.5pt] at (5.0, 3.9) {Masked Edge $(v_{\text{dev}}, C)$};
\node[font=\scriptsize\bfseries, color=green!60!black, fill=white, inner sep=1.5pt] at (8.6, 2.9) {Primary Egress};
\node[font=\scriptsize\bfseries, color=orange!80!black, fill=white, inner sep=2pt] at (4.7, 1.8) {Spur Search};
\node[font=\scriptsize\bfseries, color=orange!80!black, fill=white, inner sep=1.5pt] at (8.6, 0.7) {Spur Path};

% Description Boxes
\node[draw=green!60!black, fill=green!10, rounded corners=3pt, font=\scriptsize, align=left] at (2.2, -1.3) {
\textbf{Shortest Path $P_1$ (Dijkstra):}\\
$S \rightarrow v_{\text{dev}} \rightarrow C \rightarrow D$ (Cost = 14)
};

\node[draw=orange!80!black, fill=orange!10, rounded corners=3pt, font=\scriptsize, align=left] at (7.8, -1.3) {
\textbf{Candidate Path $P_2$ (Spur via $E$):}\\
$S \rightarrow v_{\text{dev}} \rightarrow E \rightarrow D$ (Cost = 18)\\
\textit{Loop-free candidate stored in Queue $B$}
};

\end{tikzpicture}
\caption{Loopless Candidate Route Synthesis via Yen's $K$-Shortest Paths Algorithm.}
\label{fig:yen_ksp}
\end{figure}

Yen's algorithm computes loopless paths sequentially:
\begin{enumerate}
    \item The 1st shortest path $P_1$ is obtained via standard Dijkstra search.
    \item To find path $P_k$, each node along $P_{k-1}$ serves as a deviation node $v_{\text{dev}}$. Edges participating in previous paths sharing the same root are temporarily masked from $G$.
    \item A spur path is computed from $v_{\text{dev}}$ to the destination. Concatenating root and spur produces a loopless candidate.
    \item The candidate is placed in a priority queue $B$. The shortest candidate in $B$ becomes $P_k$.
\end{enumerate}
This formulation bounds the action space to $|\mathcal{A}| = K = 4$, guaranteeing loop-freedom and ensuring $O(1)$ decision complexity.

\subsection{D3QN Neural Network Architecture}
The D3QN neural network architecture is illustrated in Figure~\ref{fig:d3qn_network}.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.82, every node/.style={transform shape},
    neuron/.style={circle, draw=blue!70!black, fill=blue!15, thick, minimum size=0.65cm, inner sep=0pt},
    valneu/.style={circle, draw=teal!70!black, fill=teal!20, thick, minimum size=0.65cm, inner sep=0pt},
    advneu/.style={circle, draw=orange!80!black, fill=orange!20, thick, minimum size=0.65cm, inner sep=0pt},
    outneu/.style={circle, draw=purple!80!black, fill=purple!20, thick, minimum size=0.65cm, inner sep=0pt},
    aggbox/.style={draw=purple!80!black, fill=purple!10, rounded corners=4pt, thick, align=center, font=\scriptsize\bfseries},
    arr/.style={->, >=Stealth, thick}
]

% Input State
\node[neuron] (i1) at (0, 2.5) {};
\node[neuron] (i2) at (0, 1.7) {};
\node[neuron] (i3) at (0, 0.9) {};
\node at (0, 0.2) {$\vdots$};
\node[neuron] (i10) at (0, -0.6) {};
\node[above=0.2cm of i1, font=\footnotesize\bfseries, align=center] {State Vector\\ $\mathbf{s} \in \mathbb{R}^{10}$};

% Shared Layer 1
\node[neuron] (h1_1) at (2.0, 2.8) {};
\node[neuron] (h1_2) at (2.0, 2.0) {};
\node[neuron] (h1_3) at (2.0, 1.2) {};
\node at (2.0, 0.4) {$\vdots$};
\node[neuron] (h1_4) at (2.0, -0.9) {};
\node[above=0.25cm of h1_1, font=\scriptsize\bfseries, align=center] {Dense 128\\ \tiny +LN +LReLU};

% Shared Layer 2
\node[neuron] (h2_1) at (4.4, 2.8) {};
\node[neuron] (h2_2) at (4.4, 2.0) {};
\node[neuron] (h2_3) at (4.4, 1.2) {};
\node at (4.4, 0.4) {$\vdots$};
\node[neuron] (h2_4) at (4.4, -0.9) {};
\node[above=0.25cm of h2_1, font=\scriptsize\bfseries, align=center] {Dense 128\\ \tiny +LN +LReLU};

% Connect Inputs to Hidden
\foreach \i in {i1,i2,i3,i10} {
    \foreach \j in {h1_1,h1_2,h1_3,h1_4} {
        \draw[gray!40] (\i) -- (\j);
    }
}
\foreach \i in {h1_1,h1_2,h1_3,h1_4} {
    \foreach \j in {h2_1,h2_2,h2_3,h2_4} {
        \draw[gray!40] (\i) -- (\j);
    }
}

% Value Stream (Upper)
\node[valneu] (v1) at (6.8, 2.5) {};
\node[valneu] (v2) at (6.8, 1.7) {};
\node[valneu] (v_out) at (8.8, 2.1) {$V$};
\node[above=0.25cm of v1, font=\scriptsize\bfseries, color=teal!70!black, align=center] {Value Stream\\ \tiny $V(s) \in \mathbb{R}$};
\foreach \i in {h2_1,h2_2} {
    \draw[teal!60] (\i) -- (v1);
    \draw[teal!60] (\i) -- (v2);
}
\draw[arr, teal!80!black] (v1) -- (v_out);
\draw[arr, teal!80!black] (v2) -- (v_out);

% Advantage Stream (Lower)
\node[advneu] (a1) at (6.8, 0.2) {};
\node[advneu] (a2) at (6.8, -0.6) {};
\node[advneu] (a3) at (6.8, -1.4) {};
\node[above=0.35cm of a1, font=\scriptsize\bfseries, color=orange!80!black, align=center] {Advantage Stream\\ \tiny $A(s, a) \in \mathbb{R}^K$};
\foreach \i in {h2_3,h2_4} {
    \draw[orange!60] (\i) -- (a1);
    \draw[orange!60] (\i) -- (a2);
    \draw[orange!60] (\i) -- (a3);
}

\node[advneu] (a_out1) at (8.8, 0.6) {$A_1$};
\node[advneu] (a_out2) at (8.8, 0.0) {$A_2$};
\node[advneu] (a_out3) at (8.8, -0.6) {$A_3$};
\node[advneu] (a_out4) at (8.8, -1.2) {$A_4$};
\foreach \i in {a1,a2,a3} {
    \draw[orange!70] (\i) -- (a_out1);
    \draw[orange!70] (\i) -- (a_out2);
    \draw[orange!70] (\i) -- (a_out3);
    \draw[orange!70] (\i) -- (a_out4);
}

% Dueling Aggregation Block
\node[aggbox, minimum width=2.4cm, minimum height=1.6cm] (agg) at (11.0, 0.6) {
Dueling Aggregation\\
\scriptsize $Q(s, a) = V(s) + {}$\\
\scriptsize $\left(A(s, a) - \frac{1}{K}\sum A\right)$
};
\draw[arr, teal!80!black] (v_out) -| (agg.north);
\draw[arr, orange!80!black] (a_out1) -- (agg.west |- a_out1);
\draw[arr, orange!80!black] (a_out2) -- (agg.west |- a_out2);
\draw[arr, orange!80!black] (a_out3) -- (agg.west |- a_out3);
\draw[arr, orange!80!black] (a_out4) -- (agg.west |- a_out4);

% Final Q outputs
\node[outneu] (q1) at (13.2, 1.5) {$Q_1$};
\node[outneu] (q2) at (13.2, 0.7) {$Q_2$};
\node[outneu] (q3) at (13.2, -0.1) {$Q_3$};
\node[outneu] (q4) at (13.2, -0.9) {$Q_4$};
\node[above=0.2cm of q1, font=\footnotesize\bfseries, color=purple!80!black] {Action Values};

\draw[arr, purple!80!black] (agg.east |- q1) -- (q1);
\draw[arr, purple!80!black] (agg.east |- q2) -- (q2);
\draw[arr, purple!80!black] (agg.east |- q3) -- (q3);
\draw[arr, purple!80!black] (agg.east |- q4) -- (q4);

\end{tikzpicture}
\caption{Dueling Double Deep Q-Network (D3QN) Architecture.}
\label{fig:d3qn_network}
\end{figure}

The network specifications are:
\begin{itemize}
    \item \textbf{Input Layer:} 10 continuous neurons accepting $\mathbf{s} \in \mathbb{R}^{10}$.
    \item \textbf{Shared Layers:} Two fully connected dense layers with 128 units each, augmented with Layer Normalization (\code{LayerNorm}) \cite{ba2016layer} and LeakyReLU activations ($\alpha = 0.01$).
    \item \textbf{Value Stream:} Dense layer (64 units) $\rightarrow$ LeakyReLU $\rightarrow$ Linear scalar output $V(s) \in \mathbb{R}$.
    \item \textbf{Advantage Stream:} Dense layer (64 units) $\rightarrow$ LeakyReLU $\rightarrow$ Linear vector output $A(s, a) \in \mathbb{R}^4$.
    \item \textbf{Aggregation Layer:} Mean-centered aggregation yielding $Q(s, a)$ via (\ref{eq:dueling_aggregation}).
\end{itemize}

\subsection{Implemented Multi-Objective Reward Function}
The controller implementation uses a weighted heuristic reward. It penalizes hops, delay, jitter, loss, and bottleneck utilization, with an additional quadratic term after a configurable threshold. This is the function used by \code{controller/routing_module.py}; it should not be interpreted as a formal safety barrier.
\begin{equation}
\label{eq:reward_full}
R(p) = -\left(w_H H(p) + w_D D(p) + w_J J(p) + w_L L(p) + \Gamma(u_{\max})\right)
\end{equation}
The checked-in defaults are $w_H=0.35$, $w_D=0.06$, $w_J=0.25$, and $w_L=0.50$. With $\theta=0.70$ and $w_C=1.0$, the congestion term is:
\begin{equation}
\label{eq:barrier_function}
\Gamma(u) = w_Cu^2 + 12w_C\max(0,u-\theta)^2.
\end{equation}
Unlike a rational or logarithmic barrier, $\Gamma$ is finite and remains well-defined when the simulator represents overload with $u>1$. The state encoder clips normalized input features to $[0,1]$, while the queue model retains overload values when estimating delay and loss. Consequently, this term encourages avoidance of loaded paths but cannot guarantee zero loss or enforce a hard capacity constraint.

\subsection{Binary SumTree Prioritized Experience Replay Architecture}
Figure~\ref{fig:sumtree_per} depicts the binary SumTree implementation of PER.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.88, every node/.style={transform shape},
    treenode/.style={circle, draw=teal!80!black, fill=teal!15, thick, minimum size=0.8cm, font=\footnotesize\bfseries, align=center},
    leafnode/.style={rectangle, draw=orange!80!black, fill=orange!20, rounded corners=3pt, thick, minimum width=1.1cm, minimum height=0.7cm, font=\scriptsize\bfseries, align=center},
    databox/.style={rectangle, draw=blue!80!black, fill=blue!10, rounded corners=2pt, thick, minimum width=1.3cm, minimum height=0.6cm, font=\tiny\ttfamily, align=center},
    arr/.style={->, >=Stealth, thick},
    treeedge/.style={thick, color=gray!70!black}
]

% Root Level 0
\node[treenode, fill=teal!30] (n0) at (6.0, 4.5) {42.8\\{\tiny $p_{\text{tot}}$}};
\node[font=\footnotesize\bfseries, color=teal!80!black] at (6.0, 5.4) {Binary SumTree: $O(\log N)$ Priority Propagation};

% Level 1
\node[treenode] (n1) at (2.6, 3.0) {28.3};
\node[treenode] (n2) at (9.4, 3.0) {14.5};
\draw[treeedge] (n0) -- (n1);
\draw[treeedge] (n0) -- (n2);

% Level 2
\node[treenode] (n3) at (1.0, 1.5) {18.1};
\node[treenode] (n4) at (4.2, 1.5) {10.2};
\node[treenode] (n5) at (7.8, 1.5) {6.4};
\node[treenode] (n6) at (11.0, 1.5) {8.1};
\draw[treeedge] (n1) -- (n3);
\draw[treeedge] (n1) -- (n4);
\draw[treeedge] (n2) -- (n5);
\draw[treeedge] (n2) -- (n6);

% Leaves Level 3
\node[leafnode] (l0) at (0.2, 0.0) {$p_1$\\12.4};
\node[leafnode] (l1) at (1.8, 0.0) {$p_2$\\5.7};
\node[leafnode] (l2) at (3.4, 0.0) {$p_3$\\2.1};
\node[leafnode] (l3) at (5.0, 0.0) {$p_4$\\8.1};
\node[leafnode] (l4) at (7.0, 0.0) {$p_5$\\1.9};
\node[leafnode] (l5) at (8.6, 0.0) {$p_6$\\4.5};
\node[leafnode] (l6) at (10.2, 0.0) {$p_7$\\3.2};
\node[leafnode] (l7) at (11.8, 0.0) {$p_8$\\4.9};

\draw[treeedge] (n3) -- (l0);
\draw[treeedge] (n3) -- (l1);
\draw[treeedge] (n4) -- (l2);
\draw[treeedge] (n4) -- (l3);
\draw[treeedge] (n5) -- (l4);
\draw[treeedge] (n5) -- (l5);
\draw[treeedge] (n6) -- (l6);
\draw[treeedge] (n6) -- (l7);

% Data Buffer Array
\node[databox] (d0) at (0.2, -1.3) {$e_1(s,a,r,s')$};
\node[databox] (d1) at (1.8, -1.3) {$e_2(s,a,r,s')$};
\node[databox] (d2) at (3.4, -1.3) {$e_3(s,a,r,s')$};
\node[databox] (d3) at (5.0, -1.3) {$e_4(s,a,r,s')$};
\node[databox] (d4) at (7.0, -1.3) {$e_5(s,a,r,s')$};
\node[databox] (d5) at (8.6, -1.3) {$e_6(s,a,r,s')$};
\node[databox] (d6) at (10.2, -1.3) {$e_7(s,a,r,s')$};
\node[databox] (d7) at (11.8, -1.3) {$e_8(s,a,r,s')$};

\draw[arr, dashed, color=blue!70!black] (l0) -- (d0);
\draw[arr, dashed, color=blue!70!black] (l1) -- (d1);
\draw[arr, dashed, color=blue!70!black] (l2) -- (d2);
\draw[arr, dashed, color=blue!70!black] (l3) -- (d3);
\draw[arr, dashed, color=blue!70!black] (l4) -- (d4);
\draw[arr, dashed, color=blue!70!black] (l5) -- (d5);
\draw[arr, dashed, color=blue!70!black] (l6) -- (d6);
\draw[arr, dashed, color=blue!70!black] (l7) -- (d7);

% Buffer caption below array
\node[font=\footnotesize\bfseries, color=blue!80!black] at (6.0, -2.1) {Circular Transition Buffer $\mathcal{D}$ (Capacity $N = 50,000$ Experiences)};

\end{tikzpicture}
\caption{Prioritized Experience Replay (PER) Binary SumTree Data Structure.}
\label{fig:sumtree_per}
\end{figure}

The buffer maintains $N = 50,000$ transitions. For batch sampling of size $B = 64$, the priority range $[0, p_{\text{total}}]$ is divided into $B$ equal ranges. A uniform random value $v_k \sim [k \cdot \frac{p_{\text{total}}}{B}, (k+1) \cdot \frac{p_{\text{total}}}{B}]$ is sampled and resolved to a leaf in $O(\log N)$ steps.

\subsection{Health-Checked Active/Standby Multi-Controller Pool}
To provide control-plane fault tolerance, the platform implements a 3-node multi-controller pool (\code{controller/ha_controller_pool.py}). Rather than employing heavyweight distributed consensus daemons (e.g., ZooKeeper or full Raft replicated state machines), the system deploys an active/standby architecture with HTTP health probing, local primary selection, and automated client failover redirection. Figure~\ref{fig:ha_failover} details the pool architecture and failover timeline.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.80, every node/.style={transform shape},
    cnode/.style={rectangle, draw=blue!80!black, fill=blue!10, rounded corners=5pt, thick, minimum width=3.4cm, minimum height=1.8cm, font=\small, align=center},
    leadernode/.style={rectangle, draw=green!60!black, fill=green!15, rounded corners=5pt, very thick, minimum width=3.6cm, minimum height=2.0cm, font=\small, align=center},
    stepbox/.style={rectangle, draw=orange!80!black, fill=orange!10, rounded corners=3pt, thick, minimum width=2.8cm, minimum height=0.9cm, font=\footnotesize\bfseries, align=center},
    arr/.style={->, >=Stealth, thick},
    darr/.style={<->, >=Stealth, thick, dashed}
]

% Cluster Nodes
\node[leadernode] (c1) at (0, 3.8) {\textbf{Primary Controller}\\ OFP: \texttt{6633}, REST: \texttt{8080}\\ Active Routing Dispatcher\\ Status: \texttt{PRIMARY}};
\node[cnode] (c2) at (-3.6, 0.4) {\textbf{Standby Backup 1}\\ OFP: \texttt{6634}, REST: \texttt{8081}\\ Ready Standby Endpoint\\ Status: \texttt{STANDBY}};
\node[cnode] (c3) at (3.6, 0.4) {\textbf{Standby Backup 2}\\ OFP: \texttt{6635}, REST: \texttt{8082}\\ Ready Standby Endpoint\\ Status: \texttt{STANDBY}};

\draw[darr, color=teal!70!black] (c1.south west) to[bend right=10] node[pos=0.5, left=2pt, font=\scriptsize\bfseries, fill=white, inner sep=2pt] {Health Probe (\texttt{/api/health})} (c2.north);
\draw[darr, color=teal!70!black] (c1.south east) to[bend left=10] node[pos=0.5, right=2pt, font=\scriptsize\bfseries, fill=white, inner sep=2pt] {Health Probe (\texttt{/api/health})} (c3.north);
\draw[darr, color=blue!60!black] (c2.east) -- node[below=3pt, font=\scriptsize\bfseries, fill=white, inner sep=2pt] {Standby Health Probe} (c3.west);

% Failover Sequence (Right side)
\node[stepbox, fill=red!15, draw=red!70!black] (s1) at (8.8, 4.0) {1. Primary Failure\\ \scriptsize{Process Stop / Connection Drop}};
\node[stepbox] (s2) at (8.8, 2.7) {2. Health Probe Failure\\ \scriptsize{Connection Refused Caught}};
\node[stepbox] (s3) at (8.8, 1.4) {3. Standby Selection\\ \scriptsize{Iterate to Next Healthy Node}};
\node[stepbox, fill=green!20, draw=green!70!black] (s4) at (8.8, 0.1) {4. Local Bookkeeping\\ \scriptsize{Promotion Latency: \textbf{0.001 ms}}};
\node[stepbox, fill=teal!20, draw=teal!70!black] (s5) at (8.8, -1.2) {5. Client HTTP Recovery\\ \scriptsize{Total Recovery: \textbf{37.96 ms}}};

\draw[arr, color=gray!70!black] (s1) -- (s2);
\draw[arr, color=gray!70!black] (s2) -- (s3);
\draw[arr, color=gray!70!black] (s3) -- (s4);
\draw[arr, color=gray!70!black] (s4) -- (s5);

\node[font=\footnotesize\bfseries, color=blue!80!black] at (0, -1.0) {Active/Standby Controller Pool ($N=3$)};
\node[font=\footnotesize\bfseries, color=gray!70!black] at (8.8, 4.8) {Measured Failover Stage Breakdown};

\end{tikzpicture}
\caption{3-Node Active/Standby Controller Pool and Failover Stage Timeline.}
\label{fig:ha_failover}
\end{figure}

\paragraph{Architecture and Failover Mechanics:}
The multi-controller pool operates as follows:
\begin{itemize}
    \item \textbf{Normal Operation:} Controller 1 serves as the active primary (OpenFlow port 6633, REST port 8080). Controllers 2 and 3 operate as warm standby nodes on separate ports (6634/8081 and 6635/8082). Open vSwitch instances are configured with multi-controller target strings (\code{tcp:127.0.0.1:6633}, \code{tcp:127.0.0.1:6634}, \code{tcp:127.0.0.1:6635}).
    \item \textbf{Health Probing and Failure Detection:} Node vitality is probed via HTTP GET \code{/api/health} with a configurable timeout ($\le 1.0$~s).
    \item \textbf{Local Promotion Bookkeeping ($0.001$~ms):} When failover is triggered, the pool updates its internal active index pointer and appends an event to the failover history log. In Python, this memory pointer reassignment and dictionary bookkeeping executes in \textbf{0.001~ms} (1.0~$\mu$s).
    \item \textbf{End-to-End Client HTTP Recovery ($37.96$~ms):} Client REST requests dispatched via \code{execute_request()} catch socket connection errors (\code{ConnectionRefusedError}, \code{URLError}) and automatically retry against the next healthy standby node, completing full end-to-end client HTTP recovery in \textbf{37.96~ms}.
    \item \textbf{Data-Plane Continuity Limitation:} Existing Open vSwitch flow entries can continue forwarding while the controller process is unavailable. This behavior was not measured as an end-to-end, loss-free failover guarantee; flows requiring new rules or state recovery may be affected.
\end{itemize}

\subsection{Closed-Loop Control Execution Timeline}
Figure~\ref{fig:control_sequence} details the millisecond-level timeline of telemetry ingestion, inference, and TCAM rule installation.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.88, every node/.style={transform shape},
    lifeline/.style={thick, dashed, color=gray!60!black},
    entity/.style={rectangle, draw=blue!80!black, fill=blue!15, rounded corners=3pt, thick, minimum width=2.4cm, minimum height=0.8cm, font=\small\bfseries, align=center},
    msg/.style={->, >=Stealth, thick},
    note/.style={rectangle, draw=teal!70!black, fill=teal!10, rounded corners=2pt, font=\scriptsize, align=center}
]

% Lifelines
\node[entity] (sw) at (0, 0) {OVS Switch\\(Data Plane)};
\node[entity] (ryu) at (4.0, 0) {Ryu Controller\\(Control Plane)};
\node[entity] (drl) at (8.0, 0) {D3QN Engine\\(AI Plane)};
\node[entity] (tcam) at (12.0, 0) {Switch TCAM\\(Flow Table 0)};

\draw[lifeline] (sw) -- (0, -7.0);
\draw[lifeline] (ryu) -- (4.0, -7.0);
\draw[lifeline] (drl) -- (8.0, -7.0);
\draw[lifeline] (tcam) -- (12.0, -7.0);

% Sequence Messages with padded badges
\draw[msg, color=blue!80!black] (4.0, -0.9) -- node[above, font=\scriptsize, fill=white, inner sep=1.5pt] {\texttt{OFPPortStatsRequest} ($\Delta t = 1.0$ s)} (0, -1.3);
\draw[msg, color=orange!80!black] (0, -1.7) -- node[above, font=\scriptsize, fill=white, inner sep=1.5pt] {\texttt{OFPPortStatsReply} (Byte/Packet deltas)} (4.0, -2.1);

\node[note] at (4.0, -2.8) {Feature Normalization\\$\mathbf{s}_t \in \mathbb{R}^{10}$ ($+0.30$ ms)};

\draw[msg, color=teal!80!black] (4.0, -3.5) -- node[above, font=\scriptsize, fill=white, inner sep=1.5pt] {Forward State $\mathbf{s}_t$} (8.0, -3.8);

\node[note] at (8.0, -4.5) {PyTorch Forward Pass\\$\arg\max Q(s,a)$ ($0.24$ ms)};

\draw[msg, color=purple!80!black] (8.0, -5.2) -- node[above, font=\scriptsize, fill=white, inner sep=1.5pt] {Selected Path $a^*$} (4.0, -5.5);
\draw[msg, color=red!70!black] (4.0, -6.0) -- node[pos=0.25, above, font=\scriptsize, fill=white, inner sep=1.5pt] {\texttt{OFPFlowMod} (\texttt{OFPFC\_MODIFY})} (12.0, -6.4);

\node[note] at (12.0, -6.8) {TCAM Rule Programmed\\Total Loop: $<3.2$ ms};

\end{tikzpicture}
\caption{End-to-End Control-Loop Telemetry and Inference Execution Timeline.}
\label{fig:control_sequence}
\end{figure}

The illustrated timing is a component-level estimate from the prototype. It excludes polling delay, controller scheduling, switch transport, and rule-application variability, so it is not an end-to-end bound.

% ----------------------------------------------------------------------------
% 4.2 EXPERIMENTS
% ----------------------------------------------------------------------------
\section{Experiments}
\label{sec:experiments}

\subsection{Evaluation Environment and Testbed Provisioning}
The evaluation testbed is provisioned on dedicated x86-64 server hardware running Ubuntu 22.04 LTS (Kernel 5.15). The software substrate integrates Ryu 4.34, Open vSwitch 2.17.0, Mininet 2.3.0, and PyTorch 2.0.1 with CUDA acceleration. Table~\ref{tab:hyperparameters} documents all neural network and training hyperparameters.

\begin{table}[htbp]
\centering
\caption{D3QN Routing Agent and PER Hyperparameter Specifications}
\label{tab:hyperparameters}
\footnotesize
\begin{tabularx}{\textwidth}{l X l}
\toprule
\textbf{Hyperparameter} & \textbf{Physical Meaning / Role} & \textbf{Configured Value} \\
\midrule
State Dimension & Number of continuous normalized features & $10$ \\
Candidate Path Action Count $K$ & Number of loopless candidate routes & $4$ \\
Shared Hidden Layers & Fully connected feature extraction layers & $2 \times 128$ units + LayerNorm \\
Stream Hidden Layers & Value and Advantage sub-stream layers & $64$ units each \\
Activation Function & Non-linear neuron activation & LeakyReLU ($\alpha = 0.01$) \\
Learning Rate $\eta$ & Adam optimizer parameter & $1.0 \times 10^{-4}$ \\
Discount Factor $\gamma$ & Temporal discount factor & $0.99$ \\
Target Soft-Update $\tau$ & Polyak tracking coefficient & $0.005$ \\
Replay Buffer Capacity $N$ & Binary SumTree transition capacity & $50,000$ \\
Batch Size $B$ & Minibatch SGD training size & $64$ \\
PER Prioritization Exponent $\alpha$ & Degree of priority sampling & $0.6$ \\
PER Importance Sampling $\beta$ & Annealed bias correction factor & $0.4 \to 1.0$ \\
PER Minimum Priority $\epsilon_{\text{per}}$ & Small constant preventing zero priority & $1.0 \times 10^{-5}$ \\
Exploration Schedule & Epsilon-greedy exploration decay & $\epsilon: 1.0 \to 0.05$ (over 3000 steps) \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{Benchmark Network Topologies}
To evaluate scalability, the platform is benchmarked across five standard topologies representing different networking domains. Figure~\ref{fig:benchmark_topos} illustrates the Fat-Tree Clos datacenter topology and the Spine-Leaf cloud fabric in TikZ.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    scale=0.78, every node/.style={transform shape},
    cnode/.style={circle, draw=red!80!black, fill=red!20, thick, minimum size=0.6cm, font=\tiny\bfseries},
    anode/.style={circle, draw=blue!80!black, fill=blue!20, thick, minimum size=0.6cm, font=\tiny\bfseries},
    enode/.style={circle, draw=green!70!black, fill=green!20, thick, minimum size=0.6cm, font=\tiny\bfseries},
    hnode/.style={rectangle, draw=gray!70!black, fill=gray!15, rounded corners=1pt, minimum width=0.45cm, minimum height=0.3cm, font=\tiny},
    link/.style={thick, color=gray!70!black}
]

% Fat-Tree Subfigure
\node[font=\small\bfseries, color=black] at (3.5, 4.3) {(a) 4-Ary Fat-Tree Clos Datacenter Topology ($k=4$)};

% Core Switches (4)
\node[cnode] (c1) at (1.0, 3.4) {$C_1$};
\node[cnode] (c2) at (2.6, 3.4) {$C_2$};
\node[cnode] (c3) at (4.4, 3.4) {$C_3$};
\node[cnode] (c4) at (6.0, 3.4) {$C_4$};

% Aggregation Switches (4)
\node[anode] (a1) at (0.6, 2.0) {$A_1$};
\node[anode] (a2) at (2.2, 2.0) {$A_2$};
\node[anode] (a3) at (4.8, 2.0) {$A_3$};
\node[anode] (a4) at (6.4, 2.0) {$A_4$};

% Edge Switches (4)
\node[enode] (e1) at (0.6, 0.7) {$E_1$};
\node[enode] (e2) at (2.2, 0.7) {$E_2$};
\node[enode] (e3) at (4.8, 0.7) {$E_3$};
\node[enode] (e4) at (6.4, 0.7) {$E_4$};

% Host Racks (8)
\foreach \i in {1,2} {
    \node[hnode] (h\i) at ({0.2 + (\i-1)*0.7}, -0.4) {$h_\i$};
    \draw[link] (e1) -- (h\i);
}
\foreach \i in {3,4} {
    \node[hnode] (h\i) at ({1.8 + (\i-3)*0.7}, -0.4) {$h_\i$};
    \draw[link] (e2) -- (h\i);
}
\foreach \i in {5,6} {
    \node[hnode] (h\i) at ({4.4 + (\i-5)*0.7}, -0.4) {$h_\i$};
    \draw[link] (e3) -- (h\i);
}
\foreach \i in {7,8} {
    \node[hnode] (h\i) at ({6.0 + (\i-7)*0.7}, -0.4) {$h_\i$};
    \draw[link] (e4) -- (h\i);
}

% Edge-Agg links
\draw[link] (e1) -- (a1); \draw[link] (e1) -- (a2);
\draw[link] (e2) -- (a1); \draw[link] (e2) -- (a2);
\draw[link] (e3) -- (a3); \draw[link] (e3) -- (a4);
\draw[link] (e4) -- (a3); \draw[link] (e4) -- (a4);

% Agg-Core links
\draw[link] (a1) -- (c1); \draw[link] (a1) -- (c2);
\draw[link] (a2) -- (c3); \draw[link] (a2) -- (c4);
\draw[link] (a3) -- (c1); \draw[link] (a3) -- (c2);
\draw[link] (a4) -- (c3); \draw[link] (a4) -- (c4);

% Spine-Leaf Subfigure (Right Side)
\begin{scope}[shift={(8.5, 0)}]
\node[font=\small\bfseries, color=black] at (3.0, 4.3) {(b) Spine-Leaf Cloud Fabric};

% Spines (3)
\node[cnode, minimum size=0.7cm] (sp1) at (1.0, 2.7) {$S_1$};
\node[cnode, minimum size=0.7cm] (sp2) at (3.0, 2.7) {$S_2$};
\node[cnode, minimum size=0.7cm] (sp3) at (5.0, 2.7) {$S_3$};

% Leaves (4)
\node[anode, minimum size=0.7cm] (lf1) at (0.3, 0.7) {$L_1$};
\node[anode, minimum size=0.7cm] (lf2) at (2.1, 0.7) {$L_2$};
\node[anode, minimum size=0.7cm] (lf3) at (3.9, 0.7) {$L_3$};
\node[anode, minimum size=0.7cm] (lf4) at (5.7, 0.7) {$L_4$};

% Full bipartite mesh
\foreach \s in {sp1, sp2, sp3} {
    \foreach \l in {lf1, lf2, lf3, lf4} {
        \draw[link] (\s) -- (\l);
    }
}
\end{scope}

\end{tikzpicture}
\caption{Architectural Layout of Benchmark Evaluation Topologies.}
\label{fig:benchmark_topos}
\end{figure}

The five benchmark topologies are:
\begin{enumerate}
    \item \textbf{Hierarchical Tree (7 Switches, 8 Hosts):} A 3-tier enterprise tree with core, distribution, and access switches.
    \item \textbf{Fat-Tree Clos (20 Switches, 16 Hosts):} A 4-ary multi-rooted datacenter fabric with 4 core, 8 aggregation, and 8 edge switches \cite{al2008scalable}.
    \item \textbf{Abilene Internet2 US Backbone (12 Switches, 15 Inter-City Links):} Real-world nationwide telecommunication backbone.
    \item \textbf{NSFNet Mesh (14 Switches, 21 Bi-Directional Links):} Classic irregular research WAN mesh.
    \item \textbf{Spine-Leaf Fabric (12 Switches, 32 Hosts):} High-density cloud datacenter fabric with full bipartite cross-connections.
\end{enumerate}

\subsection{Synthetic, Bursty, and Adversarial Traffic Generation}
Traffic workloads are generated using a multi-profile synthetic traffic engine (\code{topology/traffic_generator.sh}):
\begin{itemize}
    \item \textbf{Poisson Background Workload:} Packet inter-arrival times follow an exponential distribution with rate $\lambda_{\text{bg}}$, emulating web traffic and DNS queries.
    \item \textbf{Bursty Pareto Elephant Flows:} Heavy-tailed bursty transfers with shape parameter $\alpha = 1.2$, generating massive burst transfers that induce sudden buffer bloat.
    \item \textbf{Asymmetric Core Link Jamming:} Adversarial workload concentrating $90\%$ of traffic across a single core transit path to rigorously test proactive bypass rerouting.
\end{itemize}

\subsection{Baseline Routing Protocols for Comparative Tournament}
The D3QN platform is evaluated head-to-head against four standard routing protocols:
\begin{enumerate}
    \item \textbf{OSPF (RFC 2328) \cite{moy1998ospf}:} Standard shortest path routing using inverse capacity link weights.
    \item \textbf{Dijkstra Shortest Path First (SPF) \cite{dijkstra1959note}:} Hop-count shortest path routing.
    \item \textbf{Equal-Cost Multi-Path (ECMP):} Hash-based flow splitting across strictly equal-cost paths.
    \item \textbf{Widest Shortest Path (WSP):} Selects the path with maximum residual bottleneck capacity among minimum-hop paths.
    \item \textbf{Greedy Least-Loaded Routing (LLR):} Dynamically selects the candidate path with lowest instantaneous bottleneck utilization.
\end{enumerate}
'''
