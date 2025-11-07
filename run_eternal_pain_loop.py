#!/usr/bin/env python3

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Eternal Pain simulation in a loop, each capped at 60s, with optional plotting.",
    )
    parser.add_argument("param_set", nargs="?", default="A", help="Parameter set (e.g., A, B, C)")
    parser.add_argument("pain_delay_ms", nargs="?", type=int, default=2000, help="Pain injection delay in ms")
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
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Show a live matplotlib window that updates the analysis plot each loop",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Open the GUI window in fullscreen (if --gui)",
    )
    parser.add_argument(
        "--popup",
        action="store_true",
        help="When GUI is enabled, raise the window to front after each update",
    )
    return parser.parse_args()


class Runner:
    def __init__(self, root_dir: Path, param_set: str, pain_delay_ms: int, backend: str, timeout_s: int, gui: bool, fullscreen: bool, popup: bool):
        self.root_dir = root_dir
        self.examples_dir = root_dir / "examples"
        self.gen_script = root_dir / "eternalpain" / "c302_EternalPain.py"
        self.lems_file = f"LEMS_c302_{param_set}_EternalPain.xml"
        self.dat_file = f"c302_{param_set}_EternalPain.dat"
        self.param_set = param_set
        self.pain_delay_ms = pain_delay_ms
        self.backend = backend
        self.timeout_s = timeout_s

        # Default to not running extra matplotlib analysis; we use pynml's GUI instead
        self.show_graph = os.environ.get("SHOW_GRAPH", "0") == "1"
        self.open_graph = os.environ.get("OPEN", "0") == "1"

        self.current_pgid = None
        self.gui_enabled = gui
        self.fullscreen = fullscreen
        self.popup = popup
        self._gui = None

    def ensure_generated(self) -> None:
        if not (self.examples_dir / self.lems_file).exists():
            print(f"[INFO] Generating model: {self.lems_file}")
            self._run_checked(
                [sys.executable, str(self.gen_script), self.param_set, str(self.pain_delay_ms)],
                cwd=self.root_dir,
            )

    def run_once(self) -> None:
        print(f"[INFO] Running backend={self.backend} with timeout={self.timeout_s}s")
        if self.backend == "neuron":
            self._run_neuron()
        else:
            self._run_jnml()

        if self.show_graph:
            self._analyze_and_plot()

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

    def _analyze_and_plot(self) -> None:
        dat_path = self.examples_dir / self.dat_file
        if not dat_path.exists():
            print(f"[WARN] Data file not found: {dat_path} (skipping plot)")
            return
        print("[PLOT] Analyzing and plotting motor activity -> motor_activity_analysis.png")
        self._run_checked(
            [
                sys.executable,
                str(self.root_dir / "eternalpain" / "analyze_motor_activity.py"),
                self.dat_file,
                str(self.pain_delay_ms),
                self.lems_file,
            ],
            cwd=self.examples_dir,
        )
        if self.open_graph and (self.examples_dir / "motor_activity_analysis.png").exists():
            try:
                subprocess.Popen(["xdg-open", "motor_activity_analysis.png"], cwd=self.examples_dir)
            except Exception:
                pass
        # Update GUI if enabled
        if self.gui_enabled:
            try:
                self._ensure_gui()
                self._gui.update_image(self.examples_dir / "motor_activity_analysis.png")
            except Exception as e:
                print(f"[GUI] Failed to update GUI: {e}")

    def _ensure_gui(self) -> None:
        if self._gui is None:
            self._gui = LivePlotGUI(fullscreen=self.fullscreen)

    def _run_checked(self, cmd, cwd: Optional[Path] = None) -> None:
        print(f"[CMD] {' '.join(map(str, cmd))}")
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

    def _run_with_timeout(self, cmd, cwd: Optional[Path] = None) -> None:
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
    runner = Runner(root_dir, args.param_set, args.pain_delay_ms, args.backend, args.timeout, args.gui, args.fullscreen, args.popup)

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

    print(f"[INFO] Using PARAM_SET={runner.param_set}, PAIN_DELAY_MS={runner.pain_delay_ms}, BACKEND={runner.backend}")
    runner.ensure_generated()

    print("[INFO] Starting loop. Each run capped at 60s. Press Ctrl+C to stop.")
    while True:
        start_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[RUN] {start_ts}")
        try:
            runner.run_once()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Command failed with exit code {e.returncode}: {' '.join(e.cmd)}")
        end_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[DONE] {end_ts}")
        # Allow GUI to refresh if active
        if runner.gui_enabled and runner._gui is not None:
            runner._gui.ping()
        time.sleep(2)


class LivePlotGUI:
    """Simple non-blocking matplotlib window that shows a PNG and refreshes it."""

    def __init__(self, fullscreen: bool = False) -> None:
        import matplotlib
        import matplotlib.pyplot as plt
        import numpy as np

        matplotlib.rcParams["toolbar"] = "toolbar2"
        self.plt = plt
        self.np = np
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        if fullscreen:
            try:
                mng = plt.get_current_fig_manager()
                mng.full_screen_toggle()
            except Exception:
                pass
        plt.ion()
        self.im = None
        self.fig.canvas.manager.set_window_title("Eternal Pain Motor Activity")
        self.ax.axis("off")
        self.fig.tight_layout()
        self.fig.canvas.draw()
        self.plt.show(block=False)

    def update_image(self, path: Path) -> None:
        import matplotlib.image as mpimg
        if not path.exists():
            return
        img = mpimg.imread(str(path))
        if self.im is None:
            self.im = self.ax.imshow(img)
        else:
            self.im.set_data(img)
        self.ax.set_title(f"{path.name} @ {time.strftime('%H:%M:%S')}")
        self.fig.canvas.draw_idle()
        self.plt.pause(0.001)
        self.bring_to_front()

    def ping(self) -> None:
        # Keep UI responsive
        self.plt.pause(0.001)

    def bring_to_front(self) -> None:
        try:
            mng = self.plt.get_current_fig_manager()
            # Try Qt backends
            if hasattr(mng, "window") and mng.window is not None:
                win = mng.window
                for method_name in ("showNormal", "raise_", "activateWindow", "show"):
                    try:
                        getattr(win, method_name)()
                    except Exception:
                        pass
            # Try TkAgg
            try:
                w = self.fig.canvas.manager.window  # type: ignore[attr-defined]
                try:
                    w.attributes('-topmost', 1)
                    w.attributes('-topmost', 0)
                except Exception:
                    pass
                try:
                    w.lift()
                    w.focus_force()
                except Exception:
                    pass
            except Exception:
                pass
            # Try GTK
            try:
                w = self.fig.canvas.manager.window  # type: ignore[attr-defined]
                if hasattr(w, "present"):
                    w.present()
            except Exception:
                pass
        except Exception:
            pass


if __name__ == "__main__":
    main()


