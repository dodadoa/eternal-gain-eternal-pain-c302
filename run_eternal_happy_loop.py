#!/usr/bin/env python3

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Eternal Happiness simulation in a loop, each capped at 30s, showing pynml GUI.",
    )
    parser.add_argument("param_set", nargs="?", default="A", help="Parameter set (e.g., A, B, C)")
    parser.add_argument("reward_delay_ms", nargs="?", type=int, default=0, help="Reward onset delay in ms (if used)")
    parser.add_argument(
        "backend",
        nargs="?",
        default="jnml",
        choices=["jnml", "neuron"],
        help="Simulation backend: jnml or neuron",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Per-run timeout in seconds (default: 30)",
    )
    return parser.parse_args()


class Runner:
    def __init__(self, root_dir: Path, param_set: str, reward_delay_ms: int, backend: str, timeout_s: int):
        self.root_dir = root_dir
        self.examples_dir = root_dir / "examples"
        self.gen_script = root_dir / "eternalpain" / "c302_Happiness.py"
        self.lems_file = f"LEMS_c302_{param_set}_Happiness.xml"
        self.dat_file = f"c302_{param_set}_Happiness.dat"
        self.param_set = param_set
        self.reward_delay_ms = reward_delay_ms
        self.backend = backend
        self.timeout_s = timeout_s

        self.current_pgid = None

    def ensure_generated(self) -> None:
        if not (self.examples_dir / self.lems_file).exists():
            print(f"[INFO] Generating model: {self.lems_file}")
            self._run_checked(
                [sys.executable, str(self.gen_script), self.param_set, str(self.reward_delay_ms)],
                cwd=self.root_dir,
            )

    def run_once(self) -> None:
        print(f"[INFO] Running backend={self.backend} with timeout={self.timeout_s}s")
        if self.backend == "neuron":
            self._run_neuron()
        else:
            self._run_jnml()

    def _run_neuron(self) -> None:
        # Generate NEURON code
        self._run_checked(["pynml", self.lems_file, "-neuron"], cwd=self.examples_dir)
        # Compile mod files if present
        has_mods = any(p.suffix == ".mod" for p in self.examples_dir.glob("*.mod"))
        if has_mods:
            try:
                self._run_checked(["nrnivmodl"], cwd=self.examples_dir)
            except Exception:
                pass
        nrn_py = self.lems_file.replace(".xml", "_nrn.py")
        if not (self.examples_dir / nrn_py).exists():
            print(f"[WARN] {nrn_py} not found; skipping NEURON run.")
            return
        print(f"[INFO] Running NEURON: {nrn_py}")
        self._run_with_timeout(["nrniv", "-python", nrn_py], cwd=self.examples_dir)

    def _run_jnml(self) -> None:
        print(f"[INFO] Running jNeuroML: {self.lems_file}")
        self._run_with_timeout(["pynml", self.lems_file], cwd=self.examples_dir)

    def _run_checked(self, cmd, cwd: Path | None = None) -> None:
        print(f"[CMD] {' '.join(map(str, cmd))}")
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

    def _run_with_timeout(self, cmd, cwd: Path | None = None) -> None:
        print(f"[CMD:timeout] {' '.join(map(str, cmd))}")
        # Start in a new process group for clean SIGINT forwarding
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            preexec_fn=os.setsid,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.current_pgid = os.getpgid(proc.pid)
        try:
            try:
                stdout, stderr = proc.communicate(timeout=self.timeout_s)
                if stdout:
                    sys.stdout.write(stdout)
                if stderr:
                    sys.stderr.write(stderr)
            except subprocess.TimeoutExpired:
                print("[TIMEOUT] Sending SIGINT to process group...")
                os.killpg(self.current_pgid, signal.SIGINT)
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                    if stdout:
                        sys.stdout.write(stdout)
                    if stderr:
                        sys.stderr.write(stderr)
                except subprocess.TimeoutExpired:
                    print("[TIMEOUT] Process did not exit after SIGINT; sending SIGKILL...")
                    os.killpg(self.current_pgid, signal.SIGKILL)
        finally:
            self.current_pgid = None


def main() -> None:
    args = parse_args()
    root_dir = Path(__file__).resolve().parent
    runner = Runner(root_dir, args.param_set, args.reward_delay_ms, args.backend, args.timeout)

    # Trap SIGINT/SIGTERM to stop current run and exit
    def _handle_sig(signum, frame):
        print("\n[INTERRUPT] Caught signal. Stopping current run and exiting...")
        if runner.current_pgid is not None:
            try:
                os.killpg(runner.current_pgid, signal.SIGINT)
            except Exception:
                pass
        time.sleep(0.5)
        sys.exit(130)

    signal.signal(signal.SIGINT, _handle_sig)
    signal.signal(signal.SIGTERM, _handle_sig)

    print(f"[INFO] Using PARAM_SET={runner.param_set}, BACKEND={runner.backend}")
    runner.ensure_generated()

    print("[INFO] Starting loop. Each run capped at 30s. Press Ctrl+C to stop.")
    while True:
        start_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[RUN] {start_ts}")
        try:
            runner.run_once()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Command failed with exit code {e.returncode}: {' '.join(e.cmd)}")
        end_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[DONE] {end_ts}")
        time.sleep(2)


if __name__ == "__main__":
    main()


