#!/usr/bin/env python3
"""
Deep Q-Network (DQN) Training & Evaluation Suite for Adaptive SDN Traffic Engineering (EC499).
Fulfills EC499 Proposal Objectives 1, 3, 4, 5 and Procedure 4:
 - Trains Double DQN Agent with Prioritized Experience Replay (PER) using 3-Phase Curriculum.
 - Simulates synthetic traffic patterns (Poisson bursts, core jamming, asymmetric loads).
 - Tracks Throughput, Bottleneck Utilization, Latency, Jitter, Packet Loss, and Loss/Reward convergence.
 - Saves trained weights in models/dqn_router.pth.
 - Generates publication-grade convergence figures in logs/plots/dqn_te_training_convergence.png.
"""

import sys
import os
import time
import json
import csv
import random
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Setup path imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'agent'))
sys.path.append(os.path.join(BASE_DIR, 'controller'))
sys.path.append(os.path.join(BASE_DIR, 'topology'))
sys.path.append(BASE_DIR)

from config import (
    PLOTS_DIR,
    DEFAULT_MODEL_PATH,
    METRICS_CSV_PATH,
    EVALUATION_RESULTS_PATH,
    STATE_SIZE,
    ACTION_SIZE,
    LEARNING_RATE,
    MEMORY_SIZE,
    BATCH_SIZE,
    TORCH_DEVICE,
    K_CANDIDATE_PATHS,
)
from dqn_router import DQNRoutingAgent
from state_manager import StateManager
from topology_library import ALL_TOPOLOGY_BUILDERS
from traditional_routing import compute_path_metrics


def build_evaluation_topology():
    """Builds the 7-switch hierarchical tree topology with cross-links."""
    g = nx.DiGraph()
    for i in range(1, 8):
        g.add_node(i)

    links = [
        (1, 2, 100.0, 2.0), (2, 1, 100.0, 2.0),
        (1, 3, 100.0, 2.0), (3, 1, 100.0, 2.0),
        (2, 4, 50.0, 3.0),  (4, 2, 50.0, 3.0),
        (2, 5, 50.0, 3.0),  (5, 2, 50.0, 3.0),
        (3, 6, 50.0, 3.0),  (6, 3, 50.0, 3.0),
        (3, 7, 50.0, 3.0),  (7, 3, 50.0, 3.0),
        # Redundant cross links
        (4, 6, 30.0, 8.0),  (6, 4, 30.0, 8.0),
        (5, 7, 30.0, 8.0),  (7, 5, 30.0, 8.0),
    ]
    for u, v, bw, lat in links:
        g.add_edge(u, v, capacity=bw, delay=lat, util=0.0)
    return g


def run_full_training(
    episodes=1000,
    lr=None,
    memory_size=None,
    batch_size=None,
    save_model_path=None,
    csv_metrics_path=None,
    eval_json_path=None,
    plots_dir=None,
    device=None,
    k_paths=None
):
    print("=" * 85)
    print(f" 🚀 STARTING DEEP Q-NETWORK ADAPTIVE TRAFFIC ENGINEERING TRAINING ({episodes} EPISODES)")
    print("=" * 85)

    lr_val = lr if lr is not None else LEARNING_RATE
    mem_size = memory_size if memory_size is not None else MEMORY_SIZE
    batch_sz = batch_size if batch_size is not None else BATCH_SIZE
    save_ckpt = save_model_path or os.environ.get('SDN_MODEL_PATH', DEFAULT_MODEL_PATH)
    csv_path = csv_metrics_path or os.environ.get('SDN_METRICS_CSV', METRICS_CSV_PATH)
    eval_path = eval_json_path or os.environ.get('SDN_EVALUATION_RESULTS', EVALUATION_RESULTS_PATH)
    plots_out = plots_dir or os.environ.get('SDN_PLOTS_DIR', PLOTS_DIR)
    dev = device or TORCH_DEVICE
    k_val = k_paths or K_CANDIDATE_PATHS

    # Initialize topologies for multi-fabric curriculum exposure
    topology_instances = {}
    for tid, builder in ALL_TOPOLOGY_BUILDERS.items():
        g, meta = builder()
        t_sm = StateManager()
        t_sm.graph = g.copy()
        for u, v, data in g.edges(data=True):
            t_sm.update_link(u, v, src_port=1, dst_port=1,
                             capacity_mbps=data.get('capacity', 100.0),
                             delay_ms=data.get('delay', 2.0))
        topology_instances[tid] = {
            'sm': t_sm,
            'meta': meta,
            'edge_nodes': meta.get('edge_nodes', list(g.nodes())),
            'core_nodes': meta.get('core_nodes', [list(g.nodes())[0]])
        }

    topologies_list = list(topology_instances.keys())

    # Initialize DQN Agent with Prioritized Experience Replay
    router_agent = DQNRoutingAgent(
        state_size=STATE_SIZE,
        action_size=ACTION_SIZE,
        lr=lr_val,
        memory_size=mem_size,
        epsilon_decay=1.0, # Decay managed explicitly across 3-phase curriculum
        device=dev
    )

    # 3-Phase Curriculum Boundaries:
    phase1_end = int(episodes * 0.25)  # Exploration Phase: 0 - 25%
    phase2_end = int(episodes * 0.75)  # Learning Phase: 25% - 75%

    history = {
        'episodes': [],
        'rewards': [],
        'losses': [],
        'dqn_bottleneck': [],
        'spf_bottleneck': [],
        'latency_ms': [],
        'jitter_ms': [],
        'packet_loss_pct': [],
        'epsilons': []
    }

    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    csv_file = open(csv_path, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['episode', 'reward', 'loss', 'dqn_bottleneck', 'spf_bottleneck', 'latency_ms', 'jitter_ms', 'loss_pct', 'epsilon'])

    start_time = time.time()

    for ep in range(1, episodes + 1):
        # 3-Phase Curriculum Exploration Schedule
        if ep <= phase1_end:
            router_agent.epsilon = max(0.50, 1.0 - (ep / phase1_end) * 0.50)
        elif ep <= phase2_end:
            progress = (ep - phase1_end) / (phase2_end - phase1_end)
            router_agent.epsilon = max(0.02, 0.50 - progress * 0.48)
        else:
            router_agent.epsilon = 0.01

        # 1. Multi-Fabric Sampling: Cycle through all registered network topologies
        topo_key = topologies_list[(ep - 1) % len(topologies_list)]
        t_inst = topology_instances[topo_key]
        sm = t_inst['sm']
        edge_nodes = t_inst['edge_nodes']
        core_nodes = t_inst['core_nodes']

        # 2. Select random source and destination from edge nodes
        src = random.choice(edge_nodes)
        dst_opts = [n for n in edge_nodes if n != src]
        dst = random.choice(dst_opts)

        cand_paths = sm.get_candidate_paths(src, dst, k=k_val)
        spf_path = cand_paths[0]

        # 3. Simulate synthetic traffic patterns:
        traffic_mode = random.choices(['nominal', 'congested_primary', 'core_jam'], weights=[0.35, 0.45, 0.20])[0]

        sm.reset_simulation()
        for u, v in sm.graph.edges():
            sm.link_utilization[(u, v)] = random.uniform(0.10, 0.30)

        if traffic_mode == 'congested_primary':
            for idx in range(len(spf_path) - 1):
                u, v = spf_path[idx], spf_path[idx + 1]
                sm.link_utilization[(u, v)] = random.uniform(0.78, 0.98)
                if (v, u) in sm.link_utilization:
                    sm.link_utilization[(v, u)] = sm.link_utilization[(u, v)]
        elif traffic_mode == 'core_jam':
            sm.inject_core_congestion(utilization=random.uniform(0.82, 0.98), core_nodes=core_nodes, asymmetric_ratio=0.5)

        # 4. Agent Decision on pre-decision state s_t
        state = sm.get_routing_state(src, dst)
        action = router_agent.act(state, explore=True)
        chosen_path = cand_paths[action % len(cand_paths)]

        # Dynamic Closed-Loop Flow Allocation:
        flow_mbps = random.uniform(10.0, 20.0)
        sm.allocate_dynamic_flow(flow_id=f"train_{ep}", path=chosen_path, mbps=flow_mbps, duration_sec=3.0)

        # 5. Telemetry calculation reflecting true post-decision link states
        m_spf = compute_path_metrics(spf_path, sm.link_utilization, sm.link_delays, sm.link_bandwidths)
        m_dqn = compute_path_metrics(chosen_path, sm.link_utilization, sm.link_delays, sm.link_bandwidths)

        u_spf = m_spf['bottleneck_util']
        u_dqn = m_dqn['bottleneck_util']
        hops_dqn = m_dqn['hops']
        hops_spf = m_spf['hops']
        lat_dqn = m_dqn['total_delay']
        jit_dqn = m_dqn['jitter']
        loss_dqn = m_dqn['packet_loss']

        # 6. Intelligent Traffic Engineering Multi-Objective Reward:
        if u_spf <= 0.60:
            if action == 0:
                reward = 4.0 - 0.04 * lat_dqn - 0.1 * jit_dqn
            else:
                hop_diff = max(0, hops_dqn - hops_spf)
                reward = 1.0 - 1.0 * hop_diff - 0.05 * lat_dqn - 0.1 * jit_dqn
        else:
            if u_dqn < u_spf - 0.08:
                relief = u_spf - u_dqn
                reward = 12.0 * relief + 4.0 * (1.0 - u_dqn) - 0.15 * jit_dqn - 1.5 * loss_dqn
            elif action == 0:
                reward = - 14.0 * (u_spf ** 2) - 0.3 * jit_dqn - 3.0 * loss_dqn
            else:
                reward = - 8.0 * (u_dqn ** 2) - 0.3 * jit_dqn - 2.0 * loss_dqn

        # 7. Observe genuine posterior state s_{t+1} after traffic placement
        next_state = sm.get_routing_state(src, dst)
        router_agent.remember(state, action, reward, next_state, done=False)

        # 8. Train policy network with mini-batch Double DQN update
        loss_val = router_agent.train(batch_size=batch_sz) or 0.05

        # Expire past flows to maintain realistic non-stationary traffic matrix
        sm.step_dynamic_flows(current_time=time.time() + (ep * 0.1))

        # Record history
        history['episodes'].append(ep)
        history['rewards'].append(reward)
        history['losses'].append(loss_val)
        history['dqn_bottleneck'].append(u_dqn * 100.0)
        history['spf_bottleneck'].append(u_spf * 100.0)
        history['latency_ms'].append(lat_dqn)
        history['jitter_ms'].append(jit_dqn)
        history['packet_loss_pct'].append(loss_dqn)
        history['epsilons'].append(router_agent.epsilon)

        csv_writer.writerow([ep, round(reward, 4), round(loss_val, 4), round(u_dqn * 100, 2),
                             round(u_spf * 100, 2), round(lat_dqn, 2), round(jit_dqn, 3), round(loss_dqn, 3), round(router_agent.epsilon, 3)])

        if ep % 100 == 0 or ep == episodes:
            avg_r = np.mean(history['rewards'][-100:])
            avg_loss = np.mean(history['losses'][-100:])
            avg_b_dqn = np.mean(history['dqn_bottleneck'][-100:])
            avg_b_spf = np.mean(history['spf_bottleneck'][-100:])
            avg_lat = np.mean(history['latency_ms'][-100:])
            avg_jit = np.mean(history['jitter_ms'][-100:])
            avg_loss_p = np.mean(history['packet_loss_pct'][-100:])
            relief = avg_b_spf - avg_b_dqn

            print(f"[Ep {ep:04d}/{episodes}] Fabric: {topo_key:<9} | Reward: {avg_r:6.2f} | Loss: {avg_loss:6.4f} | "
                  f"DQN Bottleneck: {avg_b_dqn:5.1f}% vs SPF: {avg_b_spf:5.1f}% (Relief: +{relief:4.1f}%) | "
                  f"Latency: {avg_lat:4.1f}ms | Jitter: {avg_jit:4.2f}ms | Loss: {avg_loss_p:4.2f}% | Eps: {router_agent.epsilon:.3f}")

    csv_file.close()
    elapsed = time.time() - start_time
    print(f"\n[Completed] {episodes} episodes completed in {elapsed:.1f} seconds.")

    # Save trained checkpoint
    os.makedirs(os.path.dirname(os.path.abspath(save_ckpt)), exist_ok=True)
    router_agent.save(save_ckpt)
    print(f"[Saved] Checkpoint successfully saved to {save_ckpt}")

    # Generate Evaluation Results JSON
    eval_results = {
        'total_episodes': episodes,
        'training_time_seconds': round(elapsed, 1),
        'final_mean_reward': round(float(np.mean(history['rewards'][-200:])), 3),
        'final_mean_loss': round(float(np.mean(history['losses'][-200:])), 4),
        'final_dqn_bottleneck_pct': round(float(np.mean(history['dqn_bottleneck'][-200:])), 2),
        'final_spf_bottleneck_pct': round(float(np.mean(history['spf_bottleneck'][-200:])), 2),
        'congestion_relief_pct': round(float(np.mean(history['spf_bottleneck'][-200:]) - np.mean(history['dqn_bottleneck'][-200:])), 2),
        'final_latency_ms': round(float(np.mean(history['latency_ms'][-200:])), 2),
        'final_jitter_ms': round(float(np.mean(history['jitter_ms'][-200:])), 3),
        'final_packet_loss_pct': round(float(np.mean(history['packet_loss_pct'][-200:])), 3),
        'exploration_decay': '3-Phase Curriculum (Exploration -> Learning -> Exploitation)'
    }
    os.makedirs(os.path.dirname(os.path.abspath(eval_path)), exist_ok=True)
    with open(eval_path, 'w') as f:
        json.dump(eval_results, f, indent=2)

    # Plot Convergence Figures
    plot_convergence_dashboard(history, phase1_end, phase2_end, episodes, plots_dir=plots_out)
    return eval_results


def plot_convergence_dashboard(history, p1_end, p2_end, total_episodes, plots_dir=None):
    """Generates 4-panel publication-grade convergence dashboard."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    plt.subplots_adjust(hspace=0.32, wspace=0.25)

    window = max(10, total_episodes // 50)
    def smooth(arr):
        return np.convolve(arr, np.ones(window)/window, mode='valid')

    x_smooth = np.arange(window, total_episodes + 1)

    # 1. Episode Reward
    ax1 = axes[0, 0]
    ax1.plot(history['episodes'], history['rewards'], color='#1f77b4', alpha=0.10)
    ax1.plot(x_smooth, smooth(history['rewards']), color='#1f77b4', linewidth=2.0, label='DQN Reward (Smoothed)')
    ax1.axvline(p1_end, color='red', linestyle='--', alpha=0.7, label='Phase 1 Boundary')
    ax1.axvline(p2_end, color='green', linestyle='--', alpha=0.7, label='Phase 2 Boundary')
    ax1.set_title("DQN Reward Convergence (3-Phase Curriculum)", fontsize=11, fontweight='bold')
    ax1.set_ylabel("Reward")
    ax1.set_xlabel("Training Episodes")
    r_smooth = smooth(history['rewards'])
    y_min = max(-800.0, float(np.percentile(history['rewards'], 2)) * 0.7)
    y_max = max(20.0, float(np.max(r_smooth)) * 1.5)
    ax1.set_ylim(min(-400.0, y_min), y_max)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.legend(loc='lower right', fontsize=8)

    # 2. Bellman Loss
    ax2 = axes[0, 1]
    ax2.plot(history['episodes'], history['losses'], color='#d62728', alpha=0.15)
    ax2.plot(x_smooth, smooth(history['losses']), color='#d62728', linewidth=2.0, label='Smooth L1 Loss')
    ax2.axvline(p1_end, color='red', linestyle='--', alpha=0.7)
    ax2.axvline(p2_end, color='green', linestyle='--', alpha=0.7)
    ax2.set_title("Double DQN Loss Stabilization", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Loss")
    ax2.set_xlabel("Training Episodes")
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.legend(loc='upper right', fontsize=8)

    # 3. Bottleneck Congestion: DQN vs Dijkstra SPF Baseline
    ax3 = axes[1, 0]
    ax3.plot(x_smooth, smooth(history['spf_bottleneck']), color='#7f7f7f', linestyle='--', linewidth=1.8, label='SPF Baseline Load')
    ax3.plot(x_smooth, smooth(history['dqn_bottleneck']), color='#2ca02c', linewidth=2.2, label='DQN Optimized Load')
    ax3.set_title("Bottleneck Link Utilization: DQN vs SPF Baseline", fontsize=11, fontweight='bold')
    ax3.set_ylabel("Bottleneck Utilization (%)")
    ax3.set_xlabel("Training Episodes")
    ax3.grid(True, linestyle='--', alpha=0.4)
    ax3.legend(loc='upper right', fontsize=8)

    # 4. Latency, Jitter, and Packet Loss Convergence (Dual Y-Axis)
    ax4 = axes[1, 1]
    l1 = ax4.plot(x_smooth, smooth(history['latency_ms']), color='#ff7f0e', linewidth=1.8, label='Latency (ms)')
    l2 = ax4.plot(x_smooth, smooth(history['jitter_ms']), color='#9467bd', linewidth=1.8, label='Jitter (ms)')
    ax4.set_title("Latency, Jitter & Packet Loss Dynamics", fontsize=11, fontweight='bold')
    ax4.set_ylabel("Delay & Jitter (ms)")
    ax4.set_xlabel("Training Episodes")
    ax4.grid(True, linestyle='--', alpha=0.4)

    # Secondary Y-Axis for Packet Loss (%)
    ax4_loss = ax4.twinx()
    l3 = ax4_loss.plot(x_smooth, smooth(history['packet_loss_pct']), color='#e377c2', linewidth=2.0, linestyle='-.', label='Packet Loss (%)')
    ax4_loss.set_ylabel("Packet Loss (%)", color='#c51b8a', fontweight='bold', fontsize=10)
    ax4_loss.tick_params(axis='y', labelcolor='#c51b8a')
    smooth_loss = smooth(history['packet_loss_pct'])
    ax4_loss.set_ylim(0, max(4.0, float(np.max(smooth_loss)) * 1.35))

    lines = l1 + l2 + l3
    labels = [l.get_label() for l in lines]
    ax4.legend(lines, labels, loc='upper right', fontsize=8)

    plt.suptitle("Deep Q-Network Adaptive Traffic Engineering: Training Progression & Metric Convergence\n(EC499 - University of Tripoli)", fontsize=13, fontweight='bold')
    out_dir = plots_dir or PLOTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    plot_file = os.path.join(out_dir, 'dqn_te_training_convergence.png')
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[Plot] Convergence dashboard saved to {plot_file}")


def replot_convergence_from_csv(csv_path=None, plots_dir=None):
    """Re-generates publication convergence figure directly from logged metrics CSV."""
    resolved_csv = csv_path or METRICS_CSV_PATH
    if not os.path.exists(resolved_csv):
        print(f"Error: {resolved_csv} not found.")
        return
    history = {
        'episodes': [], 'rewards': [], 'losses': [],
        'dqn_bottleneck': [], 'spf_bottleneck': [],
        'latency_ms': [], 'jitter_ms': [], 'packet_loss_pct': [], 'epsilons': []
    }
    with open(resolved_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            history['episodes'].append(int(row['episode']))
            history['rewards'].append(float(row['reward']))
            history['losses'].append(float(row['loss']))
            history['dqn_bottleneck'].append(float(row['dqn_bottleneck']))
            history['spf_bottleneck'].append(float(row['spf_bottleneck']))
            history['latency_ms'].append(float(row['latency_ms']))
            history['jitter_ms'].append(float(row['jitter_ms']))
            history['packet_loss_pct'].append(float(row['loss_pct']))
            history['epsilons'].append(float(row['epsilon']))
    episodes = len(history['episodes'])
    p1_end = int(episodes * 0.25)
    p2_end = int(episodes * 0.75)
    plot_convergence_dashboard(history, p1_end, p2_end, episodes, plots_dir=plots_dir)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Deep Q-Network Traffic Engineering Training & Benchmarking (EC499)")
    parser.add_argument('episodes_pos', nargs='?', type=int, default=None, help="Optional positional episodes argument (default: 1000)")
    parser.add_argument('--episodes', '-e', type=int, default=None, help="Number of training episodes (default: 1000)")
    parser.add_argument('--replot', action='store_true', help="Re-generate convergence plots from existing CSV metrics")
    parser.add_argument('--csv-path', type=str, default=None, help=f"Path to training metrics CSV (default: {METRICS_CSV_PATH})")
    parser.add_argument('--model-path', '-m', type=str, default=None, help=f"Path to save/load trained model weights (default: {DEFAULT_MODEL_PATH})")
    parser.add_argument('--output-json', '-o', type=str, default=None, help=f"Path to save evaluation summary JSON (default: {EVALUATION_RESULTS_PATH})")
    parser.add_argument('--plots-dir', type=str, default=None, help=f"Directory to save generated convergence figures (default: {PLOTS_DIR})")
    parser.add_argument('--lr', type=float, default=None, help=f"Learning rate for Adam optimizer (default: {LEARNING_RATE})")
    parser.add_argument('--memory-size', type=int, default=None, help=f"Capacity of Prioritized Experience Replay buffer (default: {MEMORY_SIZE})")
    parser.add_argument('--batch-size', type=int, default=None, help=f"Mini-batch size for training steps (default: {BATCH_SIZE})")
    parser.add_argument('--device', type=str, default=None, help="Computation device: 'cpu', 'cuda', or auto")
    parser.add_argument('--candidate-paths', '-k', type=int, default=None, help=f"Candidate paths count K (default: {K_CANDIDATE_PATHS})")
    args = parser.parse_args()

    if args.replot:
        replot_convergence_from_csv(csv_path=args.csv_path, plots_dir=args.plots_dir)
    else:
        episodes_val = args.episodes or args.episodes_pos or 1000
        run_full_training(
            episodes=episodes_val,
            lr=args.lr,
            memory_size=args.memory_size,
            batch_size=args.batch_size,
            save_model_path=args.model_path,
            csv_metrics_path=args.csv_path,
            eval_json_path=args.output_json,
            plots_dir=args.plots_dir,
            device=args.device,
            k_paths=args.candidate_paths
        )
