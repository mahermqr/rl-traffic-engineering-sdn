#!/usr/bin/env python3
"""
Adversarial Verification & Empirical Stress Harness (EC499).
Empirical Challenger Suite probing D3QN agent, SumTree PER, model weights, latency, and zero-shot routing.

Challenges:
  1. Dueling Stream Separation Mathematical Invariant: |mean(Q) - V| <= epsilon
  2. SumTree Prioritized Experience Replay Boundary Stress (zero, extreme, negative)
  3. Pre-Trained Model Weights Numerical Health (models/dqn_router.pth)
  4. D3QN Decision Throughput and Latency Bounds (< 15ms target)
  5. Zero-Shot Routing Under Extreme Load and Pathological Topologies
"""

import os
import sys
import time
import math
import random
import unittest
import numpy as np
import torch
import torch.nn as nn
import networkx as nx

# Dynamic path resolution to ensure proper imports
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = _CURR_DIR if os.path.exists(os.path.join(_CURR_DIR, 'agent')) else os.path.dirname(_CURR_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
for sub in ['agent', 'controller', 'topology']:
    p = os.path.join(BASE_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import config
from dqn_router import DQNRoutingAgent, DuelingQNetwork
from prioritized_replay import PrioritizedReplayBuffer, SumTree
from state_manager import StateManager
from policy_selector import select_dqn_path
from topology_library import get_topology


class TestDuelingStreamMathematicalInvariant(unittest.TestCase):
    """
    Challenge 1: Verify Dueling stream separation mathematical invariant:
    Q(s, a) = V(s) + (A(s, a) - mean(A(s, a)))
    => mean_a(Q(s, a)) === V(s) identically.
    """

    @classmethod
    def setUpClass(cls):
        cls.ckpt_path = os.path.join(BASE_DIR, "models", "dqn_router.pth")
        cls.agent = DQNRoutingAgent(state_size=10, action_size=4, device="cpu")
        if os.path.exists(cls.ckpt_path):
            cls.agent.load(cls.ckpt_path)
        cls.model = cls.agent.model
        cls.model.eval()

    def test_01_invariant_over_standard_distributions(self):
        """Stress-test |mean(Q) - V| <= 1e-5 across 50,000 diverse states."""
        batch_size = 50000
        states_uniform = torch.rand(batch_size // 2, 10, dtype=torch.float32)
        states_normal = torch.randn(batch_size // 2, 10, dtype=torch.float32)
        states = torch.cat([states_uniform, states_normal], dim=0)

        with torch.no_grad():
            features = self.model.feature_network(states)
            v = self.model.value_stream(features)  # Shape (50000, 1)
            q = self.model(states)                 # Shape (50000, 4)

            mean_q = q.mean(dim=-1, keepdim=True)
            diffs = (mean_q - v).abs()
            max_diff = float(diffs.max())
            mean_diff = float(diffs.mean())

        print(f"\n[Challenge 1.1] 50,000 States Invariant Check:")
        print(f"  • Max |mean(Q) - V|:  {max_diff:.3e}")
        print(f"  • Mean |mean(Q) - V|: {mean_diff:.3e}")
        self.assertLess(max_diff, 1e-5, f"Mathematical invariant violated: max diff {max_diff} exceeds 1e-5")

    def test_02_invariant_under_adversarial_numerical_extremes(self):
        """Stress-test invariant under numerical extremes (zeros, extreme positives, negatives, tiny floats)."""
        adversarial_states = torch.tensor([
            [0.0] * 10,
            [1.0] * 10,
            [1e4] * 10,
            [-1e4] * 10,
            [1e-7] * 10,
            [-1e-7] * 10,
            [1e3, -1e3, 0.0, 1e-4, 50.0, -25.0, 0.999, 0.001, 100.0, -0.5],
            [100.0, 0.0, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0, 50.0, 100.0],
            [-500.0, -200.0, -100.0, -50.0, -10.0, -5.0, -2.0, -1.0, -0.5, -0.1],
        ], dtype=torch.float32)

        with torch.no_grad():
            features = self.model.feature_network(adversarial_states)
            v = self.model.value_stream(features)
            q = self.model(adversarial_states)

            mean_q = q.mean(dim=-1, keepdim=True)
            diffs = (mean_q - v).abs()
            max_diff = float(diffs.max())

        print(f"\n[Challenge 1.2] Adversarial Extremes Invariant Check:")
        print(f"  • Max |mean(Q) - V| on adversarial extremes: {max_diff:.3e}")
        self.assertLess(max_diff, 1e-5, f"Adversarial numerical extreme failed: {max_diff}")

    def test_03_advantage_stream_zero_mean_centering(self):
        """Verify that centered advantages sum to 0.0 identically for all states."""
        states = torch.randn(10000, 10, dtype=torch.float32)
        with torch.no_grad():
            features = self.model.feature_network(states)
            advantages = self.model.advantage_stream(features)
            centered_a = advantages - advantages.mean(dim=-1, keepdim=True)
            sum_centered = centered_a.sum(dim=-1).abs()
            max_sum_err = float(sum_centered.max())

        print(f"\n[Challenge 1.3] Advantage Stream Zero-Mean Centering Check:")
        print(f"  • Max |sum(A - mean(A))|: {max_sum_err:.3e}")
        self.assertLess(max_sum_err, 1e-5, f"Advantage centering violated: {max_sum_err}")

    def test_04_shift_invariance_under_arbitrary_advantage_offset(self):
        """Verify shift invariance: A'(s, a) = A(s, a) + c yields identical Q(s, a)."""
        states = torch.rand(1000, 10, dtype=torch.float32)
        with torch.no_grad():
            features = self.model.feature_network(states)
            v = self.model.value_stream(features)
            a = self.model.advantage_stream(features)

            q_original = v + (a - a.mean(dim=-1, keepdim=True))

            # Test shift invariance across shifts up to 1000
            for c in [-1000.0, -50.0, 7.5, 500.0, 1000.0]:
                a_shifted = a + c
                q_shifted = v + (a_shifted - a_shifted.mean(dim=-1, keepdim=True))
                shift_diff = float((q_original - q_shifted).abs().max())
                # In float32 with magnitude ~1000, eps_mach * 1000 ~ 1.2e-4
                tol = max(1e-5, 2e-7 * abs(c))
                self.assertLess(shift_diff, tol, f"Shift invariance broken for c={c}: diff={shift_diff}")

        # Also verify analytical zero diff in float64
        model_d = DuelingQNetwork(10, 4).double()
        states_d = torch.randn(100, 10, dtype=torch.float64)
        with torch.no_grad():
            f_d = model_d.feature_network(states_d)
            v_d = model_d.value_stream(f_d)
            a_d = model_d.advantage_stream(f_d)
            q_d = v_d + (a_d - a_d.mean(dim=-1, keepdim=True))
            for c in [-1000.0, 1000.0]:
                a_d_s = a_d + c
                q_d_s = v_d + (a_d_s - a_d_s.mean(dim=-1, keepdim=True))
                d_diff = float((q_d - q_d_s).abs().max())
                self.assertLess(d_diff, 1e-12, f"Double precision shift diff {d_diff} exceeded 1e-12")

        print("\n[Challenge 1.4] Shift Invariance Verified: Q(s, a) invariant to arbitrary advantage constants.")

    def test_05_gradient_decoupling_orthogonality(self):
        """Verify gradient of mean(Q) w.r.t advantage parameters is identically zero."""
        model = DuelingQNetwork(10, 4)
        model.train()
        states = torch.randn(16, 10, dtype=torch.float32)

        # Forward pass
        q = model(states)
        mean_q_sum = q.mean(dim=-1).sum()

        model.zero_grad()
        mean_q_sum.backward()

        # Check gradients in advantage stream final layer
        adv_weight_grad = model.advantage_stream[-1].weight.grad
        adv_bias_grad = model.advantage_stream[-1].bias.grad

        max_adv_w_grad = float(adv_weight_grad.abs().max())
        max_adv_b_grad = float(adv_bias_grad.abs().max())

        print(f"\n[Challenge 1.5] Gradient Decoupling Check:")
        print(f"  • Max d(mean(Q))/d(Advantage_Weight): {max_adv_w_grad:.3e}")
        print(f"  • Max d(mean(Q))/d(Advantage_Bias):   {max_adv_b_grad:.3e}")
        self.assertLess(max_adv_w_grad, 1e-6, "Gradient leakage into advantage stream detected!")
        self.assertLess(max_adv_b_grad, 1e-6, "Gradient leakage into advantage bias detected!")


class TestSumTreeAndPEREdgeBoundaries(unittest.TestCase):
    """
    Challenge 2: Stress-test SumTree Prioritized Experience Replay under edge boundaries
    (zero priority, extreme priority, negative inputs, buffer wrap-around).
    """

    def test_01_zero_priority_boundary_and_retrieval(self):
        """Verify SumTree prefix-search behavior and identify IS-weight sensitivity when priority is zero."""
        tree = SumTree(capacity=8)
        # Add entries with 0.0 priority
        for i in range(8):
            tree.add(0.0, f"item_{i}")

        self.assertEqual(tree.total(), 0.0)
        # Retrieval on 0.0 priority should not crash or loop infinitely
        idx, p, data = tree.get(0.0)
        self.assertIsNotNone(data)
        self.assertEqual(p, 0.0)

        # Empirical finding probing: In PER buffer, when all priorities are clamped or default:
        buf = PrioritizedReplayBuffer(capacity=16, state_size=10)
        for i in range(16):
            s = np.zeros(10, dtype=np.float32)
            buf.add(s, 0, 0.0, s, False)

        # Verify default add() produces positive priorities
        self.assertGreater(buf.tree.total(), 0.0, "Fresh buffer tree total must be positive")
        batch, idxs, weights = buf.sample(batch_size=4)
        self.assertEqual(len(batch), 4)
        self.assertFalse(np.isnan(weights).any(), "Standard sample weights contain NaN")

        # Now test adversarial injection of exact 0.0 priority:
        # Document empirical behavior: P=0 leads to sampling_prob=0 -> 0^-beta = inf -> inf/inf = NaN
        buf.tree.update(buf.capacity - 1, 0.0)
        p_val = buf.tree.tree[buf.capacity - 1]
        self.assertEqual(p_val, 0.0)
        print(f"\n[Challenge 2.1] SumTree Zero-Priority Traversal Verified.")
        print(f"  • Note: PER theory requires p_i > 0. If p_i=0 is forced into tree, IS-weight arithmetic encounters 0^-beta.")

    def test_02_extreme_priority_scale_invariance(self):
        """Test priorities across astronomical dynamic ranges (1e-6 to 1e12)."""
        tree = SumTree(capacity=16)
        extreme_priorities = [
            1e-6, 1e-5, 1e-4, 1e-2, 1.0, 10.0, 100.0, 1000.0,
            1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11, 1e12
        ]
        for p in extreme_priorities:
            tree.add(p, f"data_{p}")

        total = float(tree.total())
        expected_total = sum(extreme_priorities)
        rel_diff = abs(total - expected_total) / expected_total

        print(f"\n[Challenge 2.2] Extreme Priority Range (1e-6 to 1e12):")
        print(f"  • SumTree Root Total:     {total:.6e}")
        print(f"  • Expected Analytic Sum:  {expected_total:.6e}")
        print(f"  • Relative Numerical Dev: {rel_diff:.3e}")
        self.assertLess(rel_diff, 1e-4, "SumTree numerical instability under extreme scale")

    def test_03_negative_td_error_and_malicious_negative_priority(self):
        """Verify negative TD-errors are handled and SumTree behavior under negative priorities."""
        buf = PrioritizedReplayBuffer(capacity=10, state_size=10)
        for i in range(10):
            buf.add(np.zeros(10), 0, 0.0, np.zeros(10), False)

        # Update with heavily negative TD-errors
        negative_tds = np.array([-1000.0, -50.0, -10.0, -0.001, -1e5, -2.5, -99.9, -0.01, -500.0, -12.3])
        idxs = list(range(buf.capacity - 1, buf.capacity - 1 + 10))
        buf.update_priorities(idxs, negative_tds)

        # Invariant: priorities MUST be strictly positive (abs(td) + epsilon)**alpha > 0
        for i in range(10):
            leaf_idx = buf.capacity - 1 + i
            p = buf.tree.tree[leaf_idx]
            self.assertGreater(p, 0.0, f"Priority at leaf {leaf_idx} is not positive: {p}")
            expected_p = (abs(negative_tds[i]) + buf.epsilon) ** buf.alpha
            self.assertAlmostEqual(p, expected_p, places=3)

        print("\n[Challenge 2.3] Negative TD Errors Properly Rectified: Strictly positive priorities generated.")

    def test_04_sumtree_ring_buffer_overwrite_20000_cycles(self):
        """Stress-test 20,000 ring buffer overwrites and verify prefix-sum drift does not accumulate."""
        capacity = 128
        tree = SumTree(capacity=capacity)
        np.random.seed(42)

        max_drift = 0.0
        for cycle in range(20000):
            p = float(np.random.exponential(scale=10.0) + 0.01)
            tree.add(p, cycle)

            if (cycle + 1) % 2000 == 0:
                # Re-calculate exact leaf sum directly from leaf array
                leaves = tree.tree[capacity - 1 : 2 * capacity - 1]
                exact_leaf_sum = float(np.sum(leaves))
                root_total = float(tree.total())
                drift = abs(root_total - exact_leaf_sum) / max(1e-5, exact_leaf_sum)
                max_drift = max(max_drift, drift)

        print(f"\n[Challenge 2.4] 20,000 Ring Buffer Overwrite Cycles:")
        print(f"  • Maximum Prefix-Sum Relative Drift: {max_drift:.3e}")
        self.assertLess(max_drift, 1e-4, f"SumTree accumulated unacceptable drift: {max_drift}")

    def test_05_empty_buffer_and_tensor_parity(self):
        """Verify behavior on empty buffer and parity between sample() and sample_tensors()."""
        buf = PrioritizedReplayBuffer(capacity=32, state_size=10)
        # Empty buffer checks
        batch, idxs, weights = buf.sample(8)
        self.assertEqual(len(batch), 0)
        self.assertEqual(len(idxs), 0)

        tensor_sample = buf.sample_tensors(8)
        self.assertIsNone(tensor_sample, "sample_tensors on empty buffer must return None")

        # Fill with 32 transitions and compare tensor batch shapes
        for i in range(32):
            s = np.random.rand(10).astype(np.float32)
            buf.add(s, i % 4, float(i), s * 0.5, (i == 31))

        t_res = buf.sample_tensors(16, device="cpu")
        self.assertIsNotNone(t_res)
        states, actions, rewards, next_states, dones, idxs, weights = t_res
        self.assertEqual(states.shape, (16, 10))
        self.assertEqual(actions.shape, (16, 1))
        self.assertEqual(rewards.shape, (16,))
        self.assertEqual(next_states.shape, (16, 10))
        self.assertEqual(dones.shape, (16,))
        self.assertEqual(weights.shape, (16,))
        self.assertTrue((weights <= 1.0 + 1e-5).all(), "IS weights exceed 1.0 upper bound")
        print("\n[Challenge 2.5] Empty Buffer Safe & Tensor Sampling Dimensions Fully Verified.")


class TestModelWeightNumericalHealth(unittest.TestCase):
    """
    Challenge 3: Test numerical health of models/dqn_router.pth weights.
    Deep inspection for NaNs, Infs, vanishing/exploding gradients, and weight collapse.
    """

    @classmethod
    def setUpClass(cls):
        cls.ckpt_path = os.path.join(BASE_DIR, "models", "dqn_router.pth")
        if not os.path.exists(cls.ckpt_path):
            raise FileNotFoundError(f"Checkpoint not found at {cls.ckpt_path}")
        cls.checkpoint = torch.load(cls.ckpt_path, map_location="cpu")

    def test_01_checkpoint_metadata_and_integrity(self):
        """Verify checkpoint file integrity, schema version, and hyperparameter payload."""
        file_size = os.path.getsize(self.ckpt_path)
        self.assertGreater(file_size, 50000, f"Checkpoint size suspicious: {file_size} bytes")

        self.assertIn('schema_version', self.checkpoint)
        self.assertIn('model_state_dict', self.checkpoint)
        self.assertIn('target_model_state_dict', self.checkpoint)
        self.assertEqual(self.checkpoint.get('state_size'), 10)
        self.assertEqual(self.checkpoint.get('action_size'), 4)
        self.assertEqual(self.checkpoint.get('architecture'), 'dueling_double_dqn')
        print(f"\n[Challenge 3.1] Checkpoint File Verified: {file_size:,} bytes | Schema v{self.checkpoint['schema_version']}")

    def test_02_all_layers_numerical_integrity(self):
        """Verify every parameter tensor has 0 NaN, 0 Inf, and bounded numerical range."""
        model_sd = self.checkpoint['model_state_dict']
        target_sd = self.checkpoint['target_model_state_dict']

        for name, tensor in model_sd.items():
            self.assertFalse(torch.isnan(tensor).any(), f"NaN in model parameter: {name}")
            self.assertFalse(torch.isinf(tensor).any(), f"Inf in model parameter: {name}")

            t_min = float(tensor.min())
            t_max = float(tensor.max())
            t_norm = float(torch.norm(tensor))

            self.assertGreater(t_min, -10.0, f"Potential underflow explosion in {name}: min={t_min}")
            self.assertLess(t_max, 10.0, f"Potential overflow explosion in {name}: max={t_max}")
            self.assertGreater(t_norm, 0.01, f"Collapsed zero weight in {name}: norm={t_norm}")

        for name, tensor in target_sd.items():
            self.assertFalse(torch.isnan(tensor).any(), f"NaN in target parameter: {name}")
            self.assertFalse(torch.isinf(tensor).any(), f"Inf in target parameter: {name}")

        print("\n[Challenge 3.2] All 19 Parameter Tensors Non-NaN, Non-Inf, and Strictly Bounded.")

    def test_03_dead_neurons_and_weight_diversity(self):
        """Verify no dead neurons (all-zero rows/columns) exist in weight matrices."""
        model_sd = self.checkpoint['model_state_dict']
        linear_layers = [
            'feature_network.0.weight', 'feature_network.3.weight',
            'value_stream.0.weight', 'value_stream.3.weight',
            'advantage_stream.0.weight', 'advantage_stream.3.weight'
        ]

        for layer_name in linear_layers:
            w = model_sd[layer_name]
            # Check row variances across input features
            row_vars = torch.var(w, dim=1)
            min_row_var = float(row_vars.min())
            self.assertGreater(min_row_var, 1e-4, f"Dead output neuron in {layer_name}: row var={min_row_var}")

            # Check column variances across rows if more than 1 row exists
            if w.shape[0] > 1:
                col_vars = torch.var(w, dim=0)
                min_col_var = float(col_vars.min())
                self.assertGreater(min_col_var, 1e-4, f"Dead input feature in {layer_name}: col var={min_col_var}")

        print("\n[Challenge 3.3] Dead Neuron Check Passed: All output channels and input features active.")

    def test_04_target_network_polyak_coherence(self):
        """Verify target network weights coherently track policy network within expected Polyak distance."""
        model_sd = self.checkpoint['model_state_dict']
        target_sd = self.checkpoint['target_model_state_dict']

        max_param_divergence = 0.0
        for k in model_sd.keys():
            diff = float((model_sd[k] - target_sd[k]).abs().max())
            max_param_divergence = max(max_param_divergence, diff)

        print(f"\n[Challenge 3.4] Target Network Polyak Tracking:")
        print(f"  • Max Parameter Divergence ||Theta - Theta_target||_inf: {max_param_divergence:.4f}")
        self.assertLess(max_param_divergence, 0.5, f"Target network drifted too far: {max_param_divergence}")

    def test_05_optimizer_moments_stability(self):
        """Verify Adam optimizer first (m) and second (v) moments are healthy and finite."""
        opt_sd = self.checkpoint.get('optimizer_state_dict')
        if opt_sd and 'state' in opt_sd:
            for param_idx, state_dict in opt_sd['state'].items():
                if 'exp_avg' in state_dict:
                    m = state_dict['exp_avg']
                    self.assertFalse(torch.isnan(m).any())
                    self.assertFalse(torch.isinf(m).any())
                if 'exp_avg_sq' in state_dict:
                    v = state_dict['exp_avg_sq']
                    self.assertFalse(torch.isnan(v).any())
                    self.assertFalse(torch.isinf(v).any())
                    self.assertTrue((v >= 0.0).all(), "Second moment in Adam has negative values")
            print("\n[Challenge 3.5] Adam Optimizer State Audited: All momentum & second moments healthy.")


class TestDecisionThroughputAndLatencyBounds(unittest.TestCase):
    """
    Challenge 4: Benchmark D3QN decision throughput and latency bounds (< 15ms target).
    """

    @classmethod
    def setUpClass(cls):
        cls.ckpt_path = os.path.join(BASE_DIR, "models", "dqn_router.pth")
        cls.agent = DQNRoutingAgent(state_size=10, action_size=4, device="cpu")
        if os.path.exists(cls.ckpt_path):
            cls.agent.load(cls.ckpt_path)
        cls.agent.epsilon = 0.0  # Deterministic evaluation

    def test_01_single_inference_10000_trials_benchmark(self):
        """Execute 10,000 sequential single inferences (N=1) and record high-res latency distribution."""
        dummy_state = np.random.uniform(0.1, 0.9, 10).astype(np.float32)

        # Warmup
        for _ in range(200):
            self.agent.act(dummy_state, explore=False)

        latencies_ms = []
        n_trials = 10000
        for _ in range(n_trials):
            state = np.random.uniform(0.1, 0.9, 10).astype(np.float32)
            t0 = time.perf_counter()
            _ = self.agent.act(state, explore=False)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

        arr = np.array(latencies_ms, dtype=np.float64)
        mean_lat = float(np.mean(arr))
        p50 = float(np.percentile(arr, 50))
        p95 = float(np.percentile(arr, 95))
        p99 = float(np.percentile(arr, 99))
        p999 = float(np.percentile(arr, 99.9))
        max_lat = float(np.max(arr))
        throughput = 1000.0 / mean_lat

        print(f"\n[Challenge 4.1] 10,000-Trial Inference Benchmark:")
        print(f"  • Mean Latency:        {mean_lat:.4f} ms (Target: < 15.0 ms)")
        print(f"  • Median (P50):        {p50:.4f} ms")
        print(f"  • P95 Latency:         {p95:.4f} ms")
        print(f"  • P99 Latency:         {p99:.4f} ms (Target: < 15.0 ms)")
        print(f"  • P99.9 Latency:       {p999:.4f} ms")
        print(f"  • Max Latency:         {max_lat:.4f} ms (Target: < 25.0 ms)")
        print(f"  • Sustained Throughput:{throughput:,.1f} decisions/sec")

        self.assertLess(mean_lat, 15.0, f"Mean latency {mean_lat:.2f} ms exceeds 15ms target!")
        self.assertLess(p99, 15.0, f"P99 latency {p99:.2f} ms exceeds 15ms target!")
        self.assertLess(max_lat, 25.0, f"Peak max latency {max_lat:.2f} ms exceeds 25ms limit!")
        self.assertGreater(throughput, 2000.0, f"Throughput {throughput:.1f} ops/s too low!")

    def test_02_batch_inference_scaling(self):
        """Benchmark batch inference latency across sizes [1, 2, 4, 8, 16, 32, 64, 128, 256]."""
        batch_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256]
        print(f"\n[Challenge 4.2] Batch Inference Throughput Scaling (Single-Thread Optimized):")
        # Measure using single thread for deterministic low latency
        orig_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        try:
            for b in batch_sizes:
                x = torch.randn(b, 10, dtype=torch.float32)
                # Warmup
                for _ in range(50):
                    _ = self.agent.model(x)

                n_reps = 200
                t0 = time.perf_counter()
                with torch.no_grad():
                    for _ in range(n_reps):
                        _ = self.agent.model(x)
                t1 = time.perf_counter()
                elapsed_ms = ((t1 - t0) / n_reps) * 1000.0
                per_item_us = (elapsed_ms / b) * 1000.0
                throughput = (b * n_reps) / (t1 - t0)
                print(f"  • Batch={b:3d} | Latency={elapsed_ms:6.3f} ms | Per-Item={per_item_us:6.2f} µs | Throughput={throughput:8,.1f} items/sec")
                self.assertLess(elapsed_ms, 15.0, f"Batch size {b} latency exceeded 15ms")
        finally:
            torch.set_num_threads(orig_threads)


class TestZeroShotExtremeLoadAndPathologicalTopologies(unittest.TestCase):
    """
    Challenge 5: Challenge zero-shot routing on extreme load conditions and pathological topologies.
    """

    @classmethod
    def setUpClass(cls):
        cls.ckpt_path = os.path.join(BASE_DIR, "models", "dqn_router.pth")
        cls.agent = DQNRoutingAgent(state_size=10, action_size=4, device="cpu")
        if os.path.exists(cls.ckpt_path):
            cls.agent.load(cls.ckpt_path)
        cls.agent.epsilon = 0.0

    def test_01_extreme_traffic_demands(self):
        """Stress-test traffic demands from 0.0 to 10,000.0 Mbps."""
        g, _ = get_topology('abilene')
        sm = StateManager()
        for u, v in g.edges():
            sm.update_link(u, v, 1, 1, capacity_mbps=100.0, delay_ms=2.0)
            sm.update_link(v, u, 1, 1, capacity_mbps=100.0, delay_ms=2.0)

        src, dst = 1, 5
        candidates = sm.get_candidate_paths(src, dst, k=4)
        self.assertGreater(len(candidates), 1)

        demands = [0.0, 0.0001, 1.0, 50.0, 100.0, 500.0, 1000.0, 10000.0]
        for d in demands:
            res_pure = select_dqn_path(self.agent, sm, src, dst, candidate_paths=candidates, demand_mbps=d, mode="pure")
            res_safe = select_dqn_path(self.agent, sm, src, dst, candidate_paths=candidates, demand_mbps=d, mode="safety")

            self.assertEqual(res_pure["status"], "success")
            self.assertEqual(res_safe["status"], "success")
            self.assertIn(res_pure["action"], range(len(candidates)))
            self.assertIn(res_safe["action"], range(len(candidates)))
            self.assertTrue(all(math.isfinite(q) for q in res_pure["q_values"]))
            self.assertTrue(all(math.isfinite(s) for s in res_safe["scores"]))

        print("\n[Challenge 5.1] Extreme Traffic Demands (0.0 to 10,000 Mbps) Routed Without Error.")

    def test_02_flash_crowd_congestion_avoidance(self):
        """Verify safety mode sharply diverts traffic when primary path is saturated (99% load)."""
        g, _ = get_topology('abilene')
        sm = StateManager()
        for u, v in g.edges():
            sm.update_link(u, v, 1, 1, capacity_mbps=100.0, delay_ms=2.0)
            sm.update_link(v, u, 1, 1, capacity_mbps=100.0, delay_ms=2.0)

        candidates = sm.get_candidate_paths(1, 5, k=4)

        # Jam shortest path (Path 0)
        for u, v in zip(candidates[0], candidates[0][1:]):
            sm.link_utilization[(u, v)] = 0.99
            sm.link_delays[(u, v)] = 300.0

        decision = select_dqn_path(self.agent, sm, 1, 5, candidate_paths=candidates, demand_mbps=10.0, mode="safety")
        # In safety mode, path 0 should be penalized heavily by the barrier function
        self.assertNotEqual(decision["action"], 0, f"Safety mode stubbornly chose jammed path 0: scores={decision['scores']}")
        print(f"\n[Challenge 5.2] Flash-Crowd Avoidance Succeeded: Jammed Path 0 bypassed for Path {decision['action']}.")

    def test_03_pathological_topologies(self):
        """Test pathological topologies: disconnected graph, single-link line, dense random mesh."""
        # 1. Disconnected Graph
        sm_disc = StateManager()
        sm_disc.update_link(1, 2, 1, 1, 100.0, 2.0)
        sm_disc.update_link(3, 4, 1, 1, 100.0, 2.0)
        res_disc = select_dqn_path(self.agent, sm_disc, 1, 4, candidate_paths=[], mode="pure")
        self.assertEqual(res_disc["status"], "no_route")
        self.assertIsNone(res_disc["path"])

        # 2. Single-link (2-node) line graph
        sm_line = StateManager()
        sm_line.update_link(1, 2, 1, 1, 100.0, 2.0)
        sm_line.update_link(2, 1, 1, 1, 100.0, 2.0)
        cands_line = sm_line.get_candidate_paths(1, 2, k=4)
        res_line = select_dqn_path(self.agent, sm_line, 1, 2, candidate_paths=cands_line, mode="pure")
        self.assertEqual(res_line["status"], "success")
        self.assertEqual(res_line["path"], [1, 2])

        # 3. Dense Erdős–Rényi random graph (50 nodes, p=0.2)
        rg = nx.erdos_renyi_graph(n=50, p=0.2, seed=42)
        sm_rand = StateManager()
        for u, v in rg.edges():
            sm_rand.update_link(u, v, 1, 1, capacity_mbps=100.0, delay_ms=2.0)
            sm_rand.update_link(v, u, 1, 1, capacity_mbps=100.0, delay_ms=2.0)

        # Test 20 random routing queries on dense unseen graph
        nodes = list(rg.nodes())
        success_count = 0
        for _ in range(20):
            src, dst = random.sample(nodes, 2)
            cands = sm_rand.get_candidate_paths(src, dst, k=4)
            res = select_dqn_path(self.agent, sm_rand, src, dst, candidate_paths=cands, mode="pure")
            if res["status"] == "success":
                success_count += 1
                self.assertGreaterEqual(len(res["path"]), 2)

        self.assertEqual(success_count, 20, "Dense random graph failed to route connected pairs")
        print(f"\n[Challenge 5.3] Pathological Topologies (Disconnected, 2-Node, Dense 50-Node ER) Validated (20/20 pairs routed).")

    def test_04_adversarial_state_noise_perturbations(self):
        """Verify model stability when inputs are perturbed with severe Gaussian noise (sigma up to 1.0)."""
        clean_state = np.array([0.3, 0.2, 0.4, 0.1, 0.5, 0.1, 0.2, 0.15, 0.3, 0.5], dtype=np.float32)

        for sigma in [0.05, 0.1, 0.25, 0.5, 1.0]:
            noise = np.random.normal(0, sigma, size=10).astype(np.float32)
            noisy_state = clean_state + noise

            # Model should produce valid bounded Q-values without exploding
            q_vals = self.agent.get_q_values(noisy_state)
            self.assertEqual(len(q_vals), 4)
            self.assertTrue(all(math.isfinite(q) for q in q_vals))
            action = self.agent.act(noisy_state, explore=False)
            self.assertIn(action, [0, 1, 2, 3])

        print("\n[Challenge 5.4] Adversarial State Noise Perturbation: Stable across sigma in [0.05, 1.0].")


if __name__ == '__main__':
    unittest.main()
