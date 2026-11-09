# `agent/dqn_router.py`

> **File:** `agent/dqn_router.py`  
> **Subsystem / Category:** 1. Reinforcement Learning (DQN) Agent  
> **Language:** `python`  
> **Lines of Code:** 404  
> **File Size:** 18.99 KB  

---

## Overview

Dueling Double Deep Q-Network (D3QN) routing agent implementation with prioritized experience replay, epsilon-greedy exploration, and target network synchronization in PyTorch.

### Architecture & Symbols
- **Classes:** `DuelingQNetwork`, `StandardQNetwork`, `DQNRoutingAgent`
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
import os
import sys
import random
import time
from collections import deque
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# Dynamic path resolution
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_AGENT_DIR)
for _p in [_AGENT_DIR, _BASE_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import config
except ImportError:
    try:
        from .. import config
    except ImportError:
        config = None

try:
    from prioritized_replay import PrioritizedReplayBuffer
except ImportError:
    from agent.prioritized_replay import PrioritizedReplayBuffer

class DuelingQNetwork(nn.Module):
    """
    Dueling Q-Network architecture for Adaptive SDN Unicast Routing.
    Decouples state-value V(s) from candidate-path advantages A(s, a),
    enabling sharp policy differentiation in dense traffic congestion.
    """
    def __init__(self, state_size=None, action_size=None):
        super(DuelingQNetwork, self).__init__()
        self.state_size = state_size if state_size is not None else (config.STATE_SIZE if config else 10)
        self.action_size = action_size if action_size is not None else (config.ACTION_SIZE if config else 4)
        if int(self.state_size) <= 0 or int(self.action_size) <= 0:
            raise ValueError("state_size and action_size must be positive")

        self.feature_network = nn.Sequential(
            nn.Linear(self.state_size, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.LayerNorm(128),
            nn.ReLU()
        )
        self.value_stream = nn.Sequential(
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        self.advantage_stream = nn.Sequential(
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, self.action_size)
        )

    def forward(self, state):
        features = self.feature_network(state)
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)
        # Q(s, a) = V(s) + (A(s, a) - mean(A(s, a)))
        return values + (advantages - advantages.mean(dim=-1, keepdim=True))

class StandardQNetwork(nn.Module):
    """
    Standard Feedforward Q-Network (Non-Dueling baseline for ablation studies).
    Directly maps state representation to action Q-values.
    """
    def __init__(self, state_size=None, action_size=None):
        super(StandardQNetwork, self).__init__()
        self.state_size = state_size if state_size is not None else (config.STATE_SIZE if config else 10)
        self.action_size = action_size if action_size is not None else (config.ACTION_SIZE if config else 4)
        if int(self.state_size) <= 0 or int(self.action_size) <= 0:
            raise ValueError("state_size and action_size must be positive")

        self.network = nn.Sequential(
            nn.Linear(self.state_size, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, self.action_size)
        )

    def forward(self, state):
        return self.network(state)

class DQNRoutingAgent:
    """
    Dueling Double Deep Q-Network (D3QN) Agent for Adaptive SDN Unicast Routing.
    Selects optimal routing paths among K-candidate paths based on
    real-time network state (link latency, bandwidth utilization, topology features).
    Supports Prioritized Experience Replay (PER), Polyak target updates, and GPU/CPU acceleration.
    """
    def __init__(self, state_size=None, action_size=None, lr=None, gamma=None,
                 epsilon=None, epsilon_min=None, epsilon_decay=None, memory_size=None,
                 use_per=None, tau=None, target_update_freq=None, grad_clip_norm=None, device=None,
                 dueling=None, double_dqn=None):
        self.state_size = state_size if state_size is not None else (config.STATE_SIZE if config else 10)
        self.action_size = action_size if action_size is not None else (config.ACTION_SIZE if config else 4)
        self.gamma = gamma if gamma is not None else (config.GAMMA if config else 0.95)
        self.epsilon = epsilon if epsilon is not None else (config.EPSILON_START if config else 1.0)
        self.epsilon_min = epsilon_min if epsilon_min is not None else (config.EPSILON_MIN if config else 0.01)
        self.epsilon_decay = epsilon_decay if epsilon_decay is not None else (config.EPSILON_DECAY if config else 0.995)
        self.learning_rate = lr if lr is not None else (config.LEARNING_RATE if config else 0.001)
        self.use_per = use_per if use_per is not None else (config.USE_PER if config else True)
        self.tau = tau if tau is not None else (config.TAU if config else 0.005)
        self.target_update_freq = target_update_freq if target_update_freq is not None else (config.TARGET_UPDATE_FREQ if config else 10)
        self.grad_clip_norm = grad_clip_norm if grad_clip_norm is not None else (config.GRADIENT_CLIP_NORM if config else 1.0)
        self.dueling = dueling if dueling is not None else True
        self.double_dqn = double_dqn if double_dqn is not None else True

        mem_size = memory_size if memory_size is not None else (config.MEMORY_SIZE if config else 5000)
        if self.use_per:
            self.memory = PrioritizedReplayBuffer(capacity=mem_size, state_size=self.state_size)
        else:
            self.memory = deque(maxlen=mem_size)

        # Configurable device selection (supports TORCH_DEVICE env var or explicit param)
        if device is not None:
            self.device = torch.device(device)
        elif config and config.TORCH_DEVICE:
            self.device = torch.device(config.TORCH_DEVICE)
        elif os.environ.get("TORCH_DEVICE"):
            self.device = torch.device(os.environ["TORCH_DEVICE"])
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Build policy network and target network (Dueling or Standard MLP)
        self.model = self._build_model().to(self.device)
        self.target_model = self._build_model().to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.model.eval()
        self.target_model.eval()

        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.SmoothL1Loss(reduction='none' if self.use_per else 'mean')

        self.update_target_counter = 0
        self.loss_history = []
        self.checkpoint_loaded = False

    def _validated_state(self, state):
        array = np.asarray(state, dtype=np.float32)
        if array.shape != (self.state_size,):
            raise ValueError(f"Expected state shape ({self.state_size},), got {array.shape}")
        if not np.isfinite(array).all():
            raise ValueError("State contains NaN or infinite values")
        return array

    def _build_model(self):
        """Constructs Q-Network (Dueling or Standard MLP)."""
        if self.dueling:
            return DuelingQNetwork(self.state_size, self.action_size)
        return StandardQNetwork(self.state_size, self.action_size)

    def act(self, state, explore=True, candidate_count=None):
        """Epsilon-greedy action selection optimized for low decision latency."""
        selectable = self.action_size if candidate_count is None else min(self.action_size, int(candidate_count))
        if selectable <= 0:
            raise ValueError("candidate_count must be positive")
        if explore and random.random() <= self.epsilon:
            return random.randrange(selectable)

        state_tensor = torch.as_tensor(self._validated_state(state), dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return int(torch.argmax(q_values[0, :selectable]))

    def get_q_values(self, state):
        """Returns raw Q-values for all candidate path actions from the neural policy network."""
        state_tensor = torch.as_tensor(self._validated_state(state), dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state_tensor)[0]
        return [float(x) for x in q_values.cpu().numpy()]

    def remember(self, state, action, reward, next_state, done):
        """Stores experience tuple in replay memory."""
        s = self._validated_state(state)
        a = int(action)
        r = float(reward)
        ns = self._validated_state(next_state)
        d = bool(done)
        if not 0 <= a < self.action_size:
            raise ValueError(f"Action {a} is outside [0, {self.action_size})")

        if self.use_per:
            self.memory.add(s, a, r, ns, d)
        else:
            self.memory.append((s, a, r, ns, d))

    def train(self, batch_size=32):
        """Trains the policy network using Double DQN updates on a mini-batch."""
        if len(self.memory) < batch_size:
            return None

        if self.use_per:
            if hasattr(self.memory, 'sample_tensors'):
                tensor_batch = self.memory.sample_tensors(batch_size, device=self.device)
                if tensor_batch is None:
                    return None
                states, actions, rewards, next_states, dones, idxs, weights_tensor = tensor_batch
            else:
                minibatch, idxs, is_weights = self.memory.sample(batch_size)
                weights_tensor = torch.as_tensor(is_weights, dtype=torch.float32, device=self.device)
                states = torch.as_tensor(np.array([t[0] for t in minibatch]), dtype=torch.float32, device=self.device)
                actions = torch.as_tensor([t[1] for t in minibatch], dtype=torch.int64, device=self.device).unsqueeze(1)
                rewards = torch.as_tensor([t[2] for t in minibatch], dtype=torch.float32, device=self.device)
                next_states = torch.as_tensor(np.array([t[3] for t in minibatch]), dtype=torch.float32, device=self.device)
                dones = torch.as_tensor([t[4] for t in minibatch], dtype=torch.float32, device=self.device)
        else:
            minibatch = random.sample(self.memory, batch_size)
            idxs, weights_tensor = None, None
            states = torch.as_tensor(np.array([t[0] for t in minibatch]), dtype=torch.float32, device=self.device)
            actions = torch.as_tensor([t[1] for t in minibatch], dtype=torch.int64, device=self.device).unsqueeze(1)
            rewards = torch.as_tensor([t[2] for t in minibatch], dtype=torch.float32, device=self.device)
            next_states = torch.as_tensor(np.array([t[3] for t in minibatch]), dtype=torch.float32, device=self.device)
            dones = torch.as_tensor([t[4] for t in minibatch], dtype=torch.float32, device=self.device)

        self.model.train()
        # Current Q-values: Q(s, a; theta)
        current_q = self.model(states).gather(1, actions).squeeze(1)

        # Double DQN vs Single DQN target computation
        with torch.no_grad():
            if self.double_dqn:
                best_actions = self.model(next_states).argmax(1).unsqueeze(1)
                max_next_q = self.target_model(next_states).gather(1, best_actions).squeeze(1)
            else:
                max_next_q = self.target_model(next_states).max(1)[0]
            expected_q = rewards + (1.0 - dones) * self.gamma * max_next_q

        if self.use_per:
            elementwise_loss = self.criterion(current_q, expected_q)
            loss = (elementwise_loss * weights_tensor).mean()
            td_errors = (current_q - expected_q).detach().cpu().numpy()
            self.memory.update_priorities(idxs, td_errors)
        else:
            loss = self.criterion(current_q, expected_q)

        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=self.grad_clip_norm)
        self.optimizer.step()
        self.model.eval()

        loss_val = float(loss.item())
        self.loss_history.append(loss_val)

        # Decay exploration rate
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.update_target_counter += 1
        if 0.0 < self.tau <= 1.0:
            with torch.no_grad():
                for target_p, p in zip(self.target_model.parameters(), self.model.parameters()):
                    target_p.data.lerp_(p.data, self.tau)
        elif self.update_target_counter % max(1, int(self.target_update_freq)) == 0:
            self.target_model.load_state_dict(self.model.state_dict())
        return loss_val

    def set_use_per(self, enabled):
        """Safely switches replay implementations, retaining stored transitions."""
        enabled = bool(enabled)
        if enabled == self.use_per:
            return
        if self.use_per:
            transitions = [x for x in self.memory.tree.data[:len(self.memory)] if x is not None]
            capacity = self.memory.capacity
        else:
            transitions = list(self.memory)
            capacity = self.memory.maxlen or len(transitions) or 1
        self.use_per = enabled
        if enabled:
            self.memory = PrioritizedReplayBuffer(capacity=capacity, state_size=self.state_size)
            for transition in transitions:
                self.memory.add(*transition)
        else:
            self.memory = deque(transitions, maxlen=capacity)
        self.criterion = nn.SmoothL1Loss(reduction='none' if enabled else 'mean')

    def save(self, filepath=None):
        """Saves model checkpoint."""
        if filepath is None:
            filepath = config.DEFAULT_MODEL_PATH if config else "models/dqn_router.pth"
        directory = os.path.dirname(os.path.abspath(filepath))
        os.makedirs(directory, exist_ok=True)
        torch.save({
            'schema_version': 2,
            'saved_at_unix': time.time(),
            'state_size': self.state_size,
            'action_size': self.action_size,
            'architecture': 'dueling_double_dqn',
            'model_state_dict': self.model.state_dict(),
            'target_model_state_dict': self.target_model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'hyperparameters': {
                'learning_rate': self.learning_rate, 'gamma': self.gamma,
                'epsilon_min': self.epsilon_min, 'epsilon_decay': self.epsilon_decay,
                'tau': self.tau, 'target_update_freq': self.target_update_freq,
                'use_per': self.use_per,
            },
        }, filepath)

    def load(self, filepath=None):
        """Loads model checkpoint with backward compatibility for legacy weights."""
        self.checkpoint_loaded = False
        if filepath is None:
            filepath = config.DEFAULT_MODEL_PATH if config else "models/dqn_router.pth"
        if os.path.exists(filepath):
            try:
                checkpoint = torch.load(filepath, map_location=self.device, weights_only=True)
            except TypeError:
                checkpoint = torch.load(filepath, map_location=self.device)
            if checkpoint.get('state_size', self.state_size) != self.state_size:
                return False
            if checkpoint.get('action_size', self.action_size) != self.action_size:
                return False
            try:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.target_model.load_state_dict(checkpoint['target_model_state_dict'])
                if 'optimizer_state_dict' in checkpoint:
                    try:
                        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                        for state in self.optimizer.state.values():
                            for key, value in state.items():
                                if torch.is_tensor(value):
                                    state[key] = value.to(self.device)
                    except Exception:
                        pass
            except RuntimeError:
                # Gracefully load feature representation from legacy MLP checkpoint
                saved_sd = checkpoint['model_state_dict']
                if '0.weight' in saved_sd and hasattr(self.model, 'feature_network'):
                    with torch.no_grad():
                        if self.model.feature_network[0].weight.shape == saved_sd['0.weight'].shape:
                            self.model.feature_network[0].weight.copy_(saved_sd['0.weight'])
                            self.model.feature_network[0].bias.copy_(saved_sd['0.bias'])
                        if self.model.feature_network[3].weight.shape == saved_sd['3.weight'].shape:
                            self.model.feature_network[3].weight.copy_(saved_sd['3.weight'])
                            self.model.feature_network[3].bias.copy_(saved_sd['3.bias'])
                    self.target_model.load_state_dict(self.model.state_dict())
                else:
                    return False
            self.epsilon = checkpoint.get('epsilon', self.epsilon_min)
            self.checkpoint_loaded = True
            return True
        return False

# Compatibility alias
DQNAgent = DQNRoutingAgent


if __name__ == '__main__':
    print("=" * 70)
    print(" 🧠 D3QN ADAPTIVE ROUTING AGENT - STANDALONE DIAGNOSTIC & VERIFICATION")
    print("=" * 70)
    state_dim = config.STATE_SIZE if config else 10
    action_dim = config.ACTION_SIZE if config else 4
    model_path = config.DEFAULT_MODEL_PATH if (config and os.path.isabs(config.DEFAULT_MODEL_PATH)) else os.path.join(_BASE_DIR, config.DEFAULT_MODEL_PATH if config else "models/dqn_router.pth")

    agent = DQNRoutingAgent(state_size=state_dim, action_size=action_dim)
    print(f" • Device: {agent.device}")
    print(f" • Network Architecture: Dueling Double Deep Q-Network (D3QN)")
    print(f" • State Dimension: {agent.state_size} | Action Space: {agent.action_size}")
    total_params = sum(p.numel() for p in agent.model.parameters())
    print(f" • Total Parameters: {total_params:,}")

    if os.path.exists(model_path):
        success = agent.load(model_path)
        print(f" • Checkpoint: {model_path} -> {'Loaded successfully' if success else 'Failed to load'}")
    else:
        print(f" • Checkpoint: Not found at {model_path} (using randomly initialized weights)")

    # Sample forward inference test
    dummy_state = np.random.uniform(0.1, 0.9, size=agent.state_size).astype(np.float32)
    import time
    t0 = time.perf_counter()
    q_vals = agent.get_q_values(dummy_state)
    latency_ms = (time.perf_counter() - t0) * 1000
    chosen_action = agent.act(dummy_state, explore=False)

    print(f"\n --- Forward Inference Test ---")
    print(f" • Sample Input State : [{', '.join(f'{x:.2f}' for x in dummy_state[:6])} ...]")
    print(f" • Output Q-Values    : [{', '.join(f'{q:.4f}' for q in q_vals[:6])} ...]")
    print(f" • Greedy Action Chosen: Path {chosen_action} (Q = {q_vals[chosen_action]:.4f})")
    print(f" • Decision Latency    : {latency_ms:.3f} ms")
    print("=" * 70)
    print(" ✅ DQNAgent operational and healthy.")
    print("=" * 70)
```
