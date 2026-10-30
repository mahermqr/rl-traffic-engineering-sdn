#!/usr/bin/env python3
"""Run auditable Mininet/OVS traffic-engineering trials.

The runner starts a fresh Ryu process and Mininet network for every trial, applies
matched background traffic, records raw iperf/ping/OVS/controller logs, and writes
machine-readable summaries. It never synthesizes missing measurements.

Example (requires root for Mininet)::

    sudo /usr/bin/python3 reproduce_mininet_packet_experiment.py \
      --matrix --replicates 10 \
      --controller-command .venv-controller/bin/python
"""

from __future__ import annotations

import argparse
import csv
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import shutil
import socket
import subprocess
import sys
import time
from typing import Any


_curr = Path(__file__).resolve().parent
BASE_DIR = _curr if (_curr / "agent").exists() else _curr.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
DEFAULT_RAW_ROOT = BASE_DIR / "logs" / "mininet_trials"
DEFAULT_SUMMARY = BASE_DIR / "EC499report" / "report_artifacts" / "data" / "mininet_measured_trials.json"
POLICIES = ("d3qn", "llr", "spf")
PROTOCOLS = ("udp", "tcp")
TOPOLOGIES = ("tree", "fattree")
DECISION_RE = re.compile(r"Decision:\s*([0-9.]+)\s*ms")
PING_LOSS_RE = re.compile(r"([0-9.]+)% packet loss")
PING_RTT_RE = re.compile(
    r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = "
    r"([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+) ms"
)


def utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def command_version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=10, check=False)
        output = (result.stdout or result.stderr).strip().splitlines()
        return output[0] if output else "unknown"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"unavailable: {exc}"


def require_environment(controller_command: Path, dry_run: bool) -> None:
    missing = [name for name in ("mn", "ovs-vsctl", "ovs-ofctl", "iperf") if not shutil.which(name)]
    if not controller_command.is_file():
        missing.append(str(controller_command))
    if missing:
        raise SystemExit("Missing required executable(s): " + ", ".join(missing))
    # Ryu 4.34 needs Eventlet at controller startup.  Check this once before
    # allocating a 120-condition matrix so a broken virtual environment cannot
    # turn every scheduled condition into the same opaque controller failure.
    controller_check = subprocess.run(
        [str(controller_command), "-c", "import eventlet, ryu"],
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if controller_check.returncode != 0:
        detail = (controller_check.stderr or controller_check.stdout).strip().splitlines()
        explanation = detail[-1] if detail else "unknown import failure"
        raise SystemExit(
            "The controller interpreter cannot import the Ryu runtime (eventlet and ryu).\n"
            f"Interpreter: {controller_command}\n"
            f"Cause: {explanation}\n"
            "Set CONTROLLER_PYTHON to the project .venv-controller interpreter or install the missing dependency."
        )
    if not dry_run and os.geteuid() != 0:
        raise SystemExit(
            "Mininet requires root privileges. Re-run with:\n"
            f"  sudo {sys.executable} {Path(__file__).resolve()} <same arguments>"
        )


def wait_for_port(host: str, port: int, process: subprocess.Popen[str], timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Ryu exited before listening on {host}:{port} (status {process.returncode})")
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError(f"Ryu did not listen on {host}:{port} within {timeout:.0f}s")


def parse_ping(text: str) -> dict[str, float | None]:
    loss_match = PING_LOSS_RE.search(text)
    rtt_match = PING_RTT_RE.search(text)
    return {
        "packet_loss_pct": float(loss_match.group(1)) if loss_match else None,
        "rtt_min_ms": float(rtt_match.group(1)) if rtt_match else None,
        "rtt_avg_ms": float(rtt_match.group(2)) if rtt_match else None,
        "rtt_max_ms": float(rtt_match.group(3)) if rtt_match else None,
        "rtt_mdev_ms": float(rtt_match.group(4)) if rtt_match else None,
    }


def parse_iperf_csv(text: str, protocol: str) -> dict[str, float | int | None]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        try:
            row = next(csv.reader([line]))
        except csv.Error:
            continue
        if len(row) >= 9 and row[0].isdigit():
            rows.append(row)
    if not rows:
        return {
            "throughput_mbps": None,
            "jitter_ms": None,
            "lost_datagrams": None,
            "total_datagrams": None,
            "loss_pct": None,
        }
    row = rows[-1]
    result: dict[str, float | int | None] = {
        "throughput_mbps": float(row[8]) / 1_000_000.0,
        "jitter_ms": None,
        "lost_datagrams": None,
        "total_datagrams": None,
        "loss_pct": None,
    }
    if protocol == "udp" and len(row) >= 13:
        try:
            result.update(
                jitter_ms=float(row[9]),
                lost_datagrams=int(row[10]),
                total_datagrams=int(row[11]),
                loss_pct=float(row[12]),
            )
        except ValueError:
            pass
    return result


def stop_process(process: subprocess.Popen[str] | None, timeout: float = 8.0) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def topology_and_hosts(topology_name: str):
    from topology.mininet_topo import FatTreeTopology, TreeTopology

    if topology_name == "tree":
        return TreeTopology(), ("h1", "h8"), ("h2", "h7")
    return FatTreeTopology(), ("h1", "h16"), ("h2", "h15")


def controller_environment(policy: str, of_port: int, rest_port: int) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        PYTHONPATH=os.pathsep.join(
            str(path) for path in (BASE_DIR, BASE_DIR / "agent", BASE_DIR / "controller")
        ),
        SDN_RUNTIME_MODE="live",
        SDN_ROUTING_POLICY=policy,
        RL_POLICY_MODE="pure",
        # Keep the routing-policy comparison isolated from the separate
        # experimental OpenFlow fast-failover group mechanism. Otherwise group
        # programming can dominate sparse ICMP behavior on larger fabrics.
        SDN_ENABLE_FAST_FAILOVER="false",
        SDN_REST_HOST="127.0.0.1",
        SDN_REST_PORT=str(rest_port),
        SDN_CONTROLLER_PORT=str(of_port),
        SDN_DEFAULT_TOPOLOGY="tree",
    )
    return environment


def collect_ovs(net, directory: Path) -> None:
    ovs_dir = directory / "ovs"
    ovs_dir.mkdir(parents=True, exist_ok=True)
    for switch in net.switches:
        (ovs_dir / f"{switch.name}_ports.txt").write_text(
            switch.cmd(f"ovs-ofctl -O OpenFlow13 dump-ports {switch.name}"), encoding="utf-8"
        )
        (ovs_dir / f"{switch.name}_flows.txt").write_text(
            switch.cmd(f"ovs-ofctl -O OpenFlow13 dump-flows {switch.name}"), encoding="utf-8"
        )


def run_trial(
    *, run_directory: Path, trial_index: int, replicate: int, topology_name: str, policy: str,
    protocol: str, duration: int, offered_rate_mbps: float,
    background_rate_mbps: float, warmup_seconds: float, controller_command: Path,
    of_port: int, rest_port: int, scheduler: str, dry_run: bool,
) -> dict[str, Any]:
    trial_id = f"{trial_index:04d}_{topology_name}_{policy}_{protocol}"
    trial_dir = run_directory / trial_id
    trial_dir.mkdir(parents=True, exist_ok=False)
    condition = {
        "trial_id": trial_id,
        "trial_index": trial_index,
        "replicate": replicate,
        "topology": topology_name,
        "policy": policy,
        "protocol": protocol,
        "duration_sec": duration,
        "offered_rate_mbps": offered_rate_mbps if protocol == "udp" else None,
        "background_rate_mbps": background_rate_mbps,
        "warmup_sec": warmup_seconds,
        "scheduler": scheduler,
        "started_utc": utc_stamp(),
    }
    atomic_json(trial_dir / "condition.json", condition)
    if dry_run:
        return {**condition, "status": "dry_run", "raw_directory": display_path(trial_dir)}

    from mininet.link import TCLink
    from mininet.log import setLogLevel
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, RemoteController

    setLogLevel("warning")
    controller_log_path = trial_dir / "controller.log"
    controller_log = controller_log_path.open("w", encoding="utf-8")
    controller: subprocess.Popen[str] | None = None
    net = None
    primary_server = None
    path_warmup_server = None
    background_server = None
    background_client = None
    try:
        controller = subprocess.Popen(
            [str(controller_command), str(BASE_DIR / "scripts" / "ryu_manager_compat.py"),
             str(BASE_DIR / "controller" / "main_controller.py"),
             "--observe-links", "--ofp-tcp-listen-port", str(of_port)],
            cwd=BASE_DIR,
            env=controller_environment(policy, of_port, rest_port),
            stdout=controller_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_port("127.0.0.1", of_port, controller)

        topo, primary_pair, background_pair = topology_and_hosts(topology_name)
        link_class = partial(TCLink, use_hfsc=True) if scheduler == "hfsc" else TCLink
        net = Mininet(
            topo=topo,
            switch=OVSSwitch,
            controller=lambda name: RemoteController(name, ip="127.0.0.1", port=of_port),
            link=link_class,
            autoSetMacs=True,
            autoStaticArp=True,
        )
        net.start()
        time.sleep(max(2.0, warmup_seconds))
        source, destination = (net.get(name) for name in primary_pair)
        bg_source, bg_destination = (net.get(name) for name in background_pair)

        background_port = 5101
        primary_port = 5201
        background_server = bg_destination.popen(
            ["iperf", "-s", "-u", "-p", str(background_port), "-y", "C"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        time.sleep(0.5)
        background_client = bg_source.popen(
            ["iperf", "-c", bg_destination.IP(), "-u", "-p", str(background_port),
             "-b", f"{background_rate_mbps:g}M", "-t", str(duration + int(warmup_seconds) + 2),
             "-i", "1", "-y", "C"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        time.sleep(warmup_seconds)

        # Prime host learning and reactive OpenFlow rules under the same
        # background load. Sparse ICMP is insufficient on the larger Fat-Tree
        # because the controller initially lacks destination host locations;
        # a short unscored TCP stream reliably installs the selected policy
        # path without contaminating the measured transport sample.
        warmup_port = 5099
        path_warmup_server = destination.popen(
            ["iperf", "-s", "-p", str(warmup_port), "-y", "C"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        time.sleep(0.5)
        warmup_client_output = source.cmd(
            f"iperf -c {destination.IP()} -p {warmup_port} -t 2 -i 1 -y C"
        )
        stop_process(path_warmup_server, timeout=2)
        warmup_server_output = path_warmup_server.stdout.read() if path_warmup_server.stdout else ""
        (trial_dir / "path_warmup_client.csv").write_text(warmup_client_output, encoding="utf-8")
        (trial_dir / "path_warmup_server.csv").write_text(warmup_server_output, encoding="utf-8")
        time.sleep(0.5)
        ping_output = source.cmd(f"ping -q -c 10 -i 0.2 -W 1 {destination.IP()}")
        (trial_dir / "ping.txt").write_text(ping_output, encoding="utf-8")

        server_args = ["iperf", "-s", "-p", str(primary_port), "-y", "C"]
        client_args = ["iperf", "-c", destination.IP(), "-p", str(primary_port),
                       "-t", str(duration), "-i", "1", "-y", "C"]
        if protocol == "udp":
            server_args.insert(2, "-u")
            client_args = ["iperf", "-c", destination.IP(), "-u", "-b",
                           f"{offered_rate_mbps:g}M", "-p", str(primary_port),
                           "-t", str(duration), "-i", "1", "-y", "C"]
        primary_server = destination.popen(
            server_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        time.sleep(0.5)
        client_output = source.cmd(" ".join(client_args))
        time.sleep(0.5)
        stop_process(primary_server, timeout=2)
        server_output = primary_server.stdout.read() if primary_server.stdout else ""
        (trial_dir / "iperf_client.csv").write_text(client_output, encoding="utf-8")
        (trial_dir / "iperf_server.csv").write_text(server_output, encoding="utf-8")

        collect_ovs(net, trial_dir)
        stop_process(background_client, timeout=2)
        stop_process(background_server, timeout=2)
        background_client_output = background_client.stdout.read() if background_client.stdout else ""
        background_server_output = background_server.stdout.read() if background_server.stdout else ""
        (trial_dir / "background_client.csv").write_text(background_client_output, encoding="utf-8")
        (trial_dir / "background_server.csv").write_text(background_server_output, encoding="utf-8")

        controller_log.flush()
        log_text = controller_log_path.read_text(encoding="utf-8", errors="replace")
        decision_times = [float(value) for value in DECISION_RE.findall(log_text)]
        measurement = parse_iperf_csv(server_output or client_output, protocol)
        ping_measurement = parse_ping(ping_output)
        required_values = [measurement["throughput_mbps"], ping_measurement["packet_loss_pct"]]
        # At 100% ICMP loss there is correctly no RTT sample. For any partial
        # delivery, an RTT value remains mandatory.
        if ping_measurement["packet_loss_pct"] is not None and ping_measurement["packet_loss_pct"] < 100.0:
            required_values.append(ping_measurement["rtt_avg_ms"])
        if protocol == "udp":
            required_values.extend([measurement["jitter_ms"], measurement["loss_pct"]])
        result = {
            **condition,
            "status": "success" if all(value is not None for value in required_values) else "parse_error",
            **measurement,
            **ping_measurement,
            "controller_decision_count": len(decision_times),
            "controller_decision_mean_ms": sum(decision_times) / len(decision_times) if decision_times else None,
            "controller_decision_max_ms": max(decision_times) if decision_times else None,
            "completed_utc": utc_stamp(),
            "raw_directory": display_path(trial_dir),
        }
        atomic_json(trial_dir / "result.json", result)
        return result
    except Exception as exc:
        result = {
            **condition,
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "completed_utc": utc_stamp(),
            "raw_directory": display_path(trial_dir),
        }
        atomic_json(trial_dir / "result.json", result)
        return result
    finally:
        for process in (primary_server, path_warmup_server, background_client, background_server):
            stop_process(process, timeout=2)
        if net is not None:
            net.stop()
        stop_process(controller)
        controller_log.close()
        subprocess.run(["mn", "-c"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "trial_id", "trial_index", "replicate", "topology", "policy", "protocol", "status",
        "duration_sec", "offered_rate_mbps", "background_rate_mbps", "scheduler", "throughput_mbps",
        "jitter_ms", "loss_pct", "packet_loss_pct", "rtt_avg_ms",
        "controller_decision_count", "controller_decision_mean_ms", "controller_decision_max_ms",
        "raw_directory", "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_conditions(args: argparse.Namespace) -> list[tuple[int, str, str, str]]:
    if args.matrix:
        conditions = [
            (replicate, topology, policy, protocol)
            for replicate in range(1, args.replicates + 1)
            for topology in args.topologies
            for policy in args.policies
            for protocol in args.protocols
        ]
        random.Random(args.seed).shuffle(conditions)
        return conditions
    return [(1, args.topology, args.policy, args.protocol)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", action="store_true", help="run a randomized factorial trial matrix")
    parser.add_argument("--replicates", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--topology", choices=TOPOLOGIES, default="tree")
    parser.add_argument("--policy", choices=POLICIES, default="d3qn")
    parser.add_argument("--protocol", choices=PROTOCOLS, default="udp")
    parser.add_argument("--topologies", nargs="+", choices=TOPOLOGIES, default=list(TOPOLOGIES))
    parser.add_argument("--policies", nargs="+", choices=POLICIES, default=list(POLICIES))
    parser.add_argument("--protocols", nargs="+", choices=PROTOCOLS, default=list(PROTOCOLS))
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--offered-rate", type=float, default=65.0, dest="offered_rate_mbps")
    parser.add_argument("--background-rate", type=float, default=45.0, dest="background_rate_mbps")
    parser.add_argument("--warmup", type=float, default=4.0, dest="warmup_seconds")
    parser.add_argument("--scheduler", choices=("hfsc", "htb"), default="hfsc",
                        help="Mininet link scheduler; HFSC avoids HTB quantum warnings")
    parser.add_argument("--controller-port", type=int, default=6633, dest="of_port")
    parser.add_argument("--rest-port", type=int, default=18080)
    parser.add_argument("--controller-command", type=Path,
                        default=BASE_DIR / ".venv-controller" / "bin" / "python")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--dry-run", action="store_true", help="validate and materialize the trial plan only")
    args = parser.parse_args()

    if args.replicates < 1 or args.duration < 1 or args.warmup_seconds < 0:
        parser.error("replicates and duration must be positive; warmup cannot be negative")
    # Do not call ``resolve`` here: virtual-environment ``bin/python`` is a
    # symlink. Resolving it selects the base interpreter and silently drops the
    # virtual environment's Ryu/Eventlet packages.
    controller_command = args.controller_command.expanduser()
    if not controller_command.is_absolute():
        controller_command = (Path.cwd() / controller_command).absolute()
    require_environment(controller_command, args.dry_run)

    run_id = f"mininet_{utc_stamp()}_seed{args.seed}"
    run_directory = args.raw_root.expanduser().resolve() / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    conditions = build_conditions(args)
    environment = {
        "run_id": run_id,
        "created_utc": utc_stamp(),
        "seed": args.seed,
        "trial_count": len(conditions),
        "randomized_order": bool(args.matrix),
        "scheduler": args.scheduler,
        "fast_failover_enabled": False,
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "mininet": command_version(["mn", "--version"]),
        "openvswitch": command_version(["ovs-vsctl", "--version"]),
        "iperf": command_version(["iperf", "--version"]),
        "controller_command": str(controller_command),
        "controller_sha256": sha256_file(BASE_DIR / "controller" / "main_controller.py"),
        "routing_module_sha256": sha256_file(BASE_DIR / "controller" / "routing_module.py"),
        "model_sha256": sha256_file(BASE_DIR / "models" / "dqn_router.pth"),
        "conditions": [
            {"replicate": n, "topology": t, "policy": p, "protocol": r}
            for n, t, p, r in conditions
        ],
    }
    atomic_json(run_directory / "environment.json", environment)

    results: list[dict[str, Any]] = []
    for index, (replicate, topology_name, policy, protocol) in enumerate(conditions, start=1):
        print(f"[{index:03d}/{len(conditions):03d}] {topology_name} {policy} {protocol}", flush=True)
        result = run_trial(
            run_directory=run_directory, trial_index=index, replicate=replicate,
            topology_name=topology_name,
            policy=policy, protocol=protocol, duration=args.duration,
            offered_rate_mbps=args.offered_rate_mbps,
            background_rate_mbps=args.background_rate_mbps,
            warmup_seconds=args.warmup_seconds, controller_command=controller_command,
            of_port=args.of_port, rest_port=args.rest_port, scheduler=args.scheduler,
            dry_run=args.dry_run,
        )
        results.append(result)
        write_csv(run_directory / "trials.csv", results)

    payload = {"schema_version": 1, "environment": environment, "trials": results}
    atomic_json(run_directory / "summary.json", payload)
    if not args.dry_run:
        output_json = args.output_json.expanduser().resolve()
        atomic_json(output_json, payload)
        print(f"Measured summary: {output_json}")
    print(f"Raw run directory: {run_directory}")
    failures = [row for row in results if row["status"] not in {"success", "dry_run"}]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
