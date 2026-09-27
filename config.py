#!/usr/bin/env python3
"""
Centralized Configuration & Environment Management Module (EC499).
Provides zero-hardcoded configuration for Adaptive SDN Traffic Engineering:
  - Network & OpenFlow Controller parameters (IP, Ports, REST API URLs, Timeouts)
  - Deep Reinforcement Learning Hyperparameters (D3QN, Prioritized Replay, Tau)
  - Filesystem & Storage Paths (Models, Checkpoints, Logs, Plots, Telemetry JSON)
  - Traffic Engineering & Telemetry thresholds (Capacity, Latency, Loss, WCMP)

Precedence Order:
  1. Explicit CLI arguments or function call parameters (highest)
  2. Operating System Environment Variables (e.g. SDN_*, RL_*)
  3. Optional local 'config.json' file (if present)
  4. Sensible production defaults (lowest)
"""

import os
import sys
import json
from typing import Any, Dict, Optional

# Base directory: root of the project repository
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_optional_config_file() -> Dict[str, Any]:
    """Loads optional config.json from project root or user config path if present."""
    config_file_env = os.environ.get("SDN_CONFIG_FILE", os.path.join(BASE_DIR, "config.json"))
    if os.path.isfile(config_file_env):
        try:
            with open(config_file_env, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[Config] Warning: Failed to parse {config_file_env}: {e}\n")
    return {}

_FILE_CONFIG = _load_optional_config_file()

def get_config_val(key: str, env_var: Optional[str] = None, default: Any = None, cast_type: Optional[type] = None) -> Any:
    """
    Retrieves configuration value checking:
    1. Environment variable (if env_var provided and set)
    2. config.json key (if present)
    3. default value
    """
    val = None
    if env_var and env_var in os.environ:
        val = os.environ[env_var]
    elif key in _FILE_CONFIG:
        val = _FILE_CONFIG[key]
    else:
        val = default

    if val is not None and cast_type is not None:
        try:
            if cast_type == bool:
                if isinstance(val, bool):
                    return val
                return str(val).lower() in ("1", "true", "yes", "on")
            return cast_type(val)
        except (ValueError, TypeError):
            return default
    return val

# ==============================================================================
# 1. PATHS & DIRECTORIES CONFIGURATION
# ==============================================================================
MODELS_DIR = get_config_val("models_dir", "SDN_MODELS_DIR", os.path.join(BASE_DIR, "models"))
LOGS_DIR = get_config_val("logs_dir", "SDN_LOGS_DIR", os.path.join(BASE_DIR, "logs"))
PLOTS_DIR = get_config_val("plots_dir", "SDN_PLOTS_DIR", os.path.join(LOGS_DIR, "plots"))

DEFAULT_MODEL_PATH = get_config_val(
    "model_path", "SDN_MODEL_PATH", os.path.join(MODELS_DIR, "dqn_router.pth")
)
METRICS_CSV_PATH = get_config_val(
    "metrics_csv", "SDN_METRICS_CSV", os.path.join(LOGS_DIR, "training_metrics.csv")
)
TOURNAMENT_RESULTS_PATH = get_config_val(
    "tournament_results", "SDN_TOURNAMENT_RESULTS", os.path.join(LOGS_DIR, "routing_tournament_results.json")
)
STRESS_RESULTS_PATH = get_config_val(
    "stress_results", "SDN_STRESS_RESULTS", os.path.join(LOGS_DIR, "stress_test_results.json")
)
BLIND_STRESS_RESULTS_PATH = get_config_val(
    "blind_stress_results", "SDN_BLIND_STRESS_RESULTS", os.path.join(LOGS_DIR, "blind_topologies_stress_results.json")
)
EVALUATION_RESULTS_PATH = get_config_val(
    "evaluation_results", "SDN_EVALUATION_RESULTS", os.path.join(LOGS_DIR, "evaluation_results.json")
)

# Ensure directories exist
for _d in (MODELS_DIR, LOGS_DIR, PLOTS_DIR):
    os.makedirs(_d, exist_ok=True)

# ==============================================================================
# 2. NETWORK & SDN CONTROLLER CONFIGURATION
# ==============================================================================
# OpenFlow switch-controller communication
CONTROLLER_IP = str(get_config_val("controller_ip", "SDN_CONTROLLER_IP", "127.0.0.1"))
CONTROLLER_PORT = get_config_val("controller_port", "SDN_CONTROLLER_PORT", 6633, cast_type=int)

# Web Dashboard & REST Telemetry API
REST_HOST = str(get_config_val("rest_host", "SDN_REST_HOST", "0.0.0.0"))
REST_PORT = get_config_val("rest_port", "SDN_REST_PORT", 8080, cast_type=int)

# Default REST URL for clients and simulation drivers
CONTROLLER_URL = str(get_config_val(
    "controller_url", "SDN_CONTROLLER_URL", f"http://{CONTROLLER_IP if CONTROLLER_IP != '0.0.0.0' else 'localhost'}:{REST_PORT}"
))

# Telemetry sampling interval (seconds)
STATS_POLL_INTERVAL = get_config_val("poll_interval", "SDN_POLL_INTERVAL", 3.0, cast_type=float)

# OpenFlow Flow Rule Timeouts
FLOW_IDLE_TIMEOUT = get_config_val("flow_idle_timeout", "SDN_FLOW_IDLE_TIMEOUT", 60, cast_type=int)
FLOW_HARD_TIMEOUT = get_config_val("flow_hard_timeout", "SDN_FLOW_HARD_TIMEOUT", 120, cast_type=int)

# ==============================================================================
# 3. DEEP REINFORCEMENT LEARNING HYPERPARAMETERS (D3QN)
# ==============================================================================
STATE_SIZE = get_config_val("state_size", "RL_STATE_SIZE", 10, cast_type=int)
ACTION_SIZE = get_config_val("action_size", "RL_ACTION_SIZE", 4, cast_type=int)
LEARNING_RATE = get_config_val("learning_rate", "RL_LR", 0.001, cast_type=float)
GAMMA = get_config_val("gamma", "RL_GAMMA", 0.95, cast_type=float)
EPSILON_START = get_config_val("epsilon_start", "RL_EPSILON_START", 1.0, cast_type=float)
EPSILON_MIN = get_config_val("epsilon_min", "RL_EPSILON_MIN", 0.01, cast_type=float)
EPSILON_DECAY = get_config_val("epsilon_decay", "RL_EPSILON_DECAY", 0.995, cast_type=float)

# Prioritized Experience Replay (PER) & Memory
MEMORY_SIZE = get_config_val("memory_size", "RL_MEMORY_SIZE", 5000, cast_type=int)
BATCH_SIZE = get_config_val("batch_size", "RL_BATCH_SIZE", 32, cast_type=int)
USE_PER = get_config_val("use_per", "RL_USE_PER", True, cast_type=bool)
PER_ALPHA = get_config_val("per_alpha", "RL_PER_ALPHA", 0.6, cast_type=float)
PER_BETA = get_config_val("per_beta", "RL_PER_BETA", 0.4, cast_type=float)
PER_BETA_INCREMENT = get_config_val("per_beta_inc", "RL_PER_BETA_INC", 0.001, cast_type=float)

# Polyak soft target update parameter (\tau)
TAU = get_config_val("tau", "RL_TAU", 0.005, cast_type=float)
TARGET_UPDATE_FREQ = get_config_val("target_update_freq", "RL_TARGET_UPDATE_FREQ", 10, cast_type=int)
GRADIENT_CLIP_NORM = get_config_val("grad_clip_norm", "RL_GRAD_CLIP_NORM", 1.0, cast_type=float)

# Device selection: auto, cpu, cuda
TORCH_DEVICE = get_config_val("device", "TORCH_DEVICE", None)

# ==============================================================================
# 4. TRAFFIC ENGINEERING & NETWORK SIMULATION CONSTANTS
# ==============================================================================
DEFAULT_LINK_CAPACITY = get_config_val("default_link_capacity", "SDN_DEFAULT_CAPACITY", 100.0, cast_type=float) # Mbps
DEFAULT_LINK_DELAY = get_config_val("default_link_delay", "SDN_DEFAULT_DELAY", 2.0, cast_type=float)         # ms
DEFAULT_LINK_JITTER = get_config_val("default_link_jitter", "SDN_DEFAULT_JITTER", 0.25, cast_type=float)       # ms
CONGESTION_BARRIER_THRESHOLD = get_config_val("congestion_threshold", "SDN_CONGESTION_THRESHOLD", 0.70, cast_type=float) # 70%

# Weighted Cost Multi-Path (WCMP)
WCMP_BETA = get_config_val("wcmp_beta", "SDN_WCMP_BETA", 4.0, cast_type=float)
WCMP_GROUP_ID = get_config_val("wcmp_group_id", "SDN_WCMP_GROUP_ID", 500, cast_type=int)

# Traffic Engineering & Candidate Paths
K_CANDIDATE_PATHS = get_config_val("k_candidate_paths", "SDN_K_CANDIDATE_PATHS", 4, cast_type=int)
DEFAULT_PACKET_LOSS_THRESHOLD = get_config_val("packet_loss_threshold", "SDN_PACKET_LOSS_THRESHOLD", 0.05, cast_type=float)
DEFAULT_LINK_CAPACITY_MBPS = DEFAULT_LINK_CAPACITY
DEFAULT_LINK_DELAY_MS = DEFAULT_LINK_DELAY

# Default topology
DEFAULT_TOPOLOGY_ID = str(get_config_val("default_topology", "SDN_DEFAULT_TOPOLOGY", "tree"))
AVAILABLE_TOPOLOGIES = ["tree", "fattree", "abilene", "nsfnet", "spineleaf"]

def to_dict() -> Dict[str, Any]:
    """Returns all active configuration parameters as a dictionary."""
    return {
        "paths": {
            "base_dir": BASE_DIR,
            "models_dir": MODELS_DIR,
            "logs_dir": LOGS_DIR,
            "plots_dir": PLOTS_DIR,
            "default_model_path": DEFAULT_MODEL_PATH,
            "metrics_csv_path": METRICS_CSV_PATH,
            "tournament_results_path": TOURNAMENT_RESULTS_PATH,
            "stress_results_path": STRESS_RESULTS_PATH,
            "blind_stress_results_path": BLIND_STRESS_RESULTS_PATH,
            "evaluation_results_path": EVALUATION_RESULTS_PATH
        },
        "network": {
            "controller_ip": CONTROLLER_IP,
            "controller_port": CONTROLLER_PORT,
            "rest_host": REST_HOST,
            "rest_port": REST_PORT,
            "controller_url": CONTROLLER_URL,
            "poll_interval": STATS_POLL_INTERVAL,
            "flow_idle_timeout": FLOW_IDLE_TIMEOUT,
            "flow_hard_timeout": FLOW_HARD_TIMEOUT
        },
        "rl": {
            "state_size": STATE_SIZE,
            "action_size": ACTION_SIZE,
            "learning_rate": LEARNING_RATE,
            "gamma": GAMMA,
            "epsilon_start": EPSILON_START,
            "epsilon_min": EPSILON_MIN,
            "epsilon_decay": EPSILON_DECAY,
            "memory_size": MEMORY_SIZE,
            "batch_size": BATCH_SIZE,
            "use_per": USE_PER,
            "per_alpha": PER_ALPHA,
            "per_beta": PER_BETA,
            "per_beta_increment": PER_BETA_INCREMENT,
            "tau": TAU,
            "target_update_freq": TARGET_UPDATE_FREQ,
            "grad_clip_norm": GRADIENT_CLIP_NORM,
            "device": TORCH_DEVICE
        },
        "traffic_engineering": {
            "default_link_capacity": DEFAULT_LINK_CAPACITY,
            "default_link_delay": DEFAULT_LINK_DELAY,
            "default_link_jitter": DEFAULT_LINK_JITTER,
            "congestion_barrier_threshold": CONGESTION_BARRIER_THRESHOLD,
            "wcmp_beta": WCMP_BETA,
            "wcmp_group_id": WCMP_GROUP_ID,
            "default_topology_id": DEFAULT_TOPOLOGY_ID,
            "available_topologies": AVAILABLE_TOPOLOGIES
        }
    }

if __name__ == "__main__":
    print(json.dumps(to_dict(), indent=2))
