import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
import numpy as np
import os
import sys

# Dynamic config resolution
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

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

class DQNRoutingAgent:
    """
    Dueling Double Deep Q-Network (D3QN) Agent for Adaptive SDN Unicast Routing.
    Selects optimal routing paths among K-candidate paths based on
    real-time network state (link latency, bandwidth utilization, topology features).
    Supports Prioritized Experience Replay (PER), Polyak target updates, and GPU/CPU acceleration.
    """
    def __init__(self, state_size=None, action_size=None, lr=None, gamma=None,
                 epsilon=None, epsilon_min=None, epsilon_decay=None, memory_size=None,
                 use_per=None, tau=None, target_update_freq=None, grad_clip_norm=None, device=None):
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

        # Build policy network and target network (Dueling Architecture)
        self.model = self._build_model().to(self.device)
        self.target_model = self._build_model().to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.model.eval()
        self.target_model.eval()

        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.SmoothL1Loss(reduction='none' if self.use_per else 'mean')

        self.update_target_counter = 0
        self.loss_history = []

    def _build_model(self):
        """Constructs Dueling Q-Network with Layer Normalization."""
        return DuelingQNetwork(self.state_size, self.action_size)

    def act(self, state, explore=True):
        """Epsilon-greedy action selection optimized for low decision latency."""
        if explore and random.random() <= self.epsilon:
            return random.randrange(self.action_size)

        state_tensor = torch.as_tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return int(torch.argmax(q_values[0]))

    def get_q_values(self, state):
        """Returns raw Q-values for all candidate path actions from the neural policy network."""
        state_tensor = torch.as_tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state_tensor)[0]
        return [float(x) for x in q_values.cpu().numpy()]

    def remember(self, state, action, reward, next_state, done):
        """Stores experience tuple in replay memory."""
        s = np.asarray(state, dtype=np.float32)
        a = int(action)
        r = float(reward)
        ns = np.asarray(next_state, dtype=np.float32)
        d = bool(done)

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

        # Double DQN target computation
        with torch.no_grad():
            best_actions = self.model(next_states).argmax(1).unsqueeze(1)
            max_next_q = self.target_model(next_states).gather(1, best_actions).squeeze(1)
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

        # Continuous Polyak soft target update (in-place lerp_ primitive):
        # \theta_{target} \leftarrow \tau \theta_{policy} + (1 - \tau) \theta_{target}
        with torch.no_grad():
            for target_p, p in zip(self.target_model.parameters(), self.model.parameters()):
                target_p.data.lerp_(p.data, self.tau)

        self.update_target_counter += 1
        return loss_val

    def get_q_values(self, state):
        """Returns raw Q-values for all candidate actions for a given state vector."""
        state_tensor = torch.as_tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            q_vals = self.model(state_tensor).squeeze(0).cpu().numpy()
        return q_vals

    def save(self, filepath=None):
        """Saves model checkpoint."""
        if filepath is None:
            filepath = config.DEFAULT_MODEL_PATH if config else "models/dqn_router.pth"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'target_model_state_dict': self.target_model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, filepath)

    def load(self, filepath=None):
        """Loads model checkpoint with backward compatibility for legacy weights."""
        if filepath is None:
            filepath = config.DEFAULT_MODEL_PATH if config else "models/dqn_router.pth"
        if os.path.exists(filepath):
            checkpoint = torch.load(filepath, map_location=self.device)
            try:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.target_model.load_state_dict(checkpoint['target_model_state_dict'])
                if 'optimizer_state_dict' in checkpoint:
                    try:
                        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
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
            return True
        return False
