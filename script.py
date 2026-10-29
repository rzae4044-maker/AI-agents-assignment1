import matplotlib

"""
Simple Random Walk & The Gambler's Ruin Problem
================================================
Academic Simulation & Probabilistic Analysis Engine

Author: Elite Software Consultant & Data Science Specialist
Course: Stochastic Processes & Probability Theory (Undergraduate/Graduate)
Project: "Simple Random Walk & The Gambler's Ruin Problem"

This module provides an end-to-end computational and statistical toolkit for
analyzing discrete-time simple random walks with absorbing barriers (The Gambler's
Ruin Problem). It features:
1. Exact analytical solvers for theoretical ruin probabilities and expected stopping times.
2. High-performance Monte Carlo simulation engine with confidence interval estimation.
3. Parametric sweeps across initial capital and step transition probabilities.
4. Publication-grade visualization routines using Matplotlib.

Mathematical Foundations:
- Process: S_n = s + \\sum_{i=1}^n \\xi_i, where P(\\xi_i = +1) = p, P(\\xi_i = -1) = q = 1 - p.
- State Space: S = {0, 1, ..., N}, with absorbing boundaries at 0 (Ruin) and N (Target).
- Ruin Probability:
    * Symmetric (p = 0.5): R_s = 1 - s / N
    * Asymmetric (p != 0.5): R_s = ((q/p)^s - (q/p)^N) / (1 - (q/p)^N)
- Expected Duration E[T | S_0 = s]:
    * Symmetric (p = 0.5): D_s = s * (N - s)
    * Asymmetric (p != 0.5): D_s = (1 / (q - p)) * [ s - N * (1 - (q/p)^s) / (1 - (q/p)^N) ]
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


# ==============================================================================
# 1. Theoretical Analytical Calculations
# ==============================================================================

class GamblersRuinTheory:
    """Exact analytical solutions for the classical Gambler's Ruin Problem."""

    @staticmethod
    def ruin_probability(s: int, N: int, p: float) -> float:
        """
        Calculate the exact analytical probability of ruin starting from capital s.

        Parameters
        ----------
        s : int
            Initial capital of the gambler (0 <= s <= N).
        N : int
            Target capital (total capital in system, absorbing barrier).
        p : float
            Probability of winning each step (0 < p < 1).

        Returns
        -------
        float
            Theoretical probability of ruin (absorption at 0).
        """
        if s <= 0:
            return 1.0
        if s >= N:
            return 0.0
        if np.isclose(p, 0.5):
            return 1.0 - (s / N)

        q = 1.0 - p
        lambda_ratio = q / p
        return (lambda_ratio**s - lambda_ratio**N) / (1.0 - lambda_ratio**N)

    @staticmethod
    def win_probability(s: int, N: int, p: float) -> float:
        """Calculate the exact analytical probability of reaching target N."""
        return 1.0 - GamblersRuinTheory.ruin_probability(s, N, p)

    @staticmethod
    def expected_duration(s: int, N: int, p: float) -> float:
        """
        Calculate the expected stopping time E[T | S_0 = s] until absorption.

        Parameters
        ----------
        s : int
            Initial capital of the gambler.
        N : int
            Target capital.
        p : float
            Probability of winning each step.

        Returns
        -------
        float
            Expected number of steps until absorption at 0 or N.
        """
        if s <= 0 or s >= N:
            return 0.0

        if np.isclose(p, 0.5):
            return float(s * (N - s))

        q = 1.0 - p
        lambda_ratio = q / p
        numerator = 1.0 - (lambda_ratio**s)
        denominator = 1.0 - (lambda_ratio**N)
        return (1.0 / (q - p)) * (s - N * (numerator / denominator))


# ==============================================================================
# 2. Monte Carlo Simulation Engine
# ==============================================================================

@dataclass
class SimulationResult:
    """Encapsulates statistical outputs from a Monte Carlo simulation run."""
    initial_capital: int
    target_capital: int
    win_probability: float
    num_trials: int
    empirical_ruin_prob: float
    empirical_win_prob: float
    standard_error: float
    confidence_interval_95: Tuple[float, float]
    theoretical_ruin_prob: float
    theoretical_win_prob: float
    empirical_mean_duration: float
    theoretical_mean_duration: float
    sample_paths: List[np.ndarray]


class MonteCarloEngine:
    """High-performance stochastic simulation engine for 1D random walks."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        """Initialize the random generator with an optional reproducible seed."""
        self.rng = np.random.default_rng(seed)

    def simulate_single_path(
        self, s: int, N: int, p: float, max_steps: int = 100_000
    ) -> Tuple[bool, int, np.ndarray]:
        """
        Simulate an individual random walk trajectory until absorption or max_steps.

        Parameters
        ----------
        s : int
            Initial capital.
        N : int
            Target fortune.
        p : float
            Probability of positive step.
        max_steps : int
            Cutoff safety limit to prevent infinite loops in unbounded walks.

        Returns
        -------
        Tuple[bool, int, np.ndarray]
            (is_ruined, total_steps, trajectory_array)
        """
        path = [s]
        current_pos = s

        while 0 < current_pos < N and len(path) <= max_steps:
            step = 1 if self.rng.random() < p else -1
            current_pos += step
            path.append(current_pos)

        is_ruined = (current_pos == 0)
        return is_ruined, len(path) - 1, np.array(path, dtype=np.int32)

    def run_simulation(
        self,
        s: int,
        N: int,
        p: float,
        num_trials: int = 10_000,
        max_sample_paths: int = 50,
        max_steps: int = 100_000,
    ) -> SimulationResult:
        """
        Execute an ensemble Monte Carlo simulation and aggregate statistics.

        Parameters
        ----------
        s : int
            Initial capital.
        N : int
            Target capital.
        p : float
            Win probability.
        num_trials : int
            Total number of simulated game paths.
        max_sample_paths : int
            Maximum number of trajectory arrays preserved for plotting.
        max_steps : int
            Step cutoff limit per path.

        Returns
        -------
        SimulationResult
            Comprehensive statistical record comparing empirical vs. theoretical metrics.
        """
        ruin_count = 0
        durations = np.zeros(num_trials, dtype=np.float64)
        sample_paths: List[np.ndarray] = []

        for i in range(num_trials):
            is_ruined, steps, path = self.simulate_single_path(s, N, p, max_steps)
            if is_ruined:
                ruin_count += 1
            durations[i] = steps

            if len(sample_paths) < max_sample_paths:
                sample_paths.append(path)

        empirical_ruin = ruin_count / num_trials
        empirical_win = 1.0 - empirical_ruin
        std_error = np.sqrt((empirical_ruin * (1.0 - empirical_ruin)) / num_trials)
        ci_95 = (
            max(0.0, empirical_ruin - 1.96 * std_error),
            min(1.0, empirical_ruin + 1.96 * std_error),
        )

        theo_ruin = GamblersRuinTheory.ruin_probability(s, N, p)
        theo_win = GamblersRuinTheory.win_probability(s, N, p)
        theo_duration = GamblersRuinTheory.expected_duration(s, N, p)

        return SimulationResult(
            initial_capital=s,
            target_capital=N,
            win_probability=p,
            num_trials=num_trials,
            empirical_ruin_prob=empirical_ruin,
            empirical_win_prob=empirical_win,
            standard_error=std_error,
            confidence_interval_95=ci_95,
            theoretical_ruin_prob=theo_ruin,
            theoretical_win_prob=theo_win,
            empirical_mean_duration=float(np.mean(durations)),
            theoretical_mean_duration=theo_duration,
            sample_paths=sample_paths,
        )


# ==============================================================================
# 3. Parametric Sweeps & Verification
# ==============================================================================

def sweep_capital_range(
    N: int, p: float, num_trials: int = 5_000, seed: int = 42
) -> Dict[str, np.ndarray]:
    """
    Evaluate empirical and theoretical ruin metrics across all starting capitals s in [1, N-1].
    """
    engine = MonteCarloEngine(seed=seed)
    capitals = np.arange(1, N)
    emp_ruin = np.zeros(len(capitals))
    theo_ruin = np.zeros(len(capitals))
    emp_dur = np.zeros(len(capitals))
    theo_dur = np.zeros(len(capitals))

    for idx, s in enumerate(capitals):
        res = engine.run_simulation(s=int(s), N=N, p=p, num_trials=num_trials, max_sample_paths=0)
        emp_ruin[idx] = res.empirical_ruin_prob
        theo_ruin[idx] = res.theoretical_ruin_prob
        emp_dur[idx] = res.empirical_mean_duration
        theo_dur[idx] = res.theoretical_mean_duration

    return {
        "capitals": capitals,
        "empirical_ruin": emp_ruin,
        "theoretical_ruin": theo_ruin,
        "empirical_duration": emp_dur,
        "theoretical_duration": theo_dur,
    }


def evaluate_convergence(
    s: int, N: int, p: float, trial_steps: List[int], seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Track empirical ruin probability error decay as sample size M increases.
    """
    engine = MonteCarloEngine(seed=seed)
    theo_ruin = GamblersRuinTheory.ruin_probability(s, N, p)
    errors = []

    for m in trial_steps:
        res = engine.run_simulation(s=s, N=N, p=p, num_trials=m, max_sample_paths=0)
        errors.append(abs(res.empirical_ruin_prob - theo_ruin))

    return np.array(trial_steps), np.array(errors), theo_ruin


# ==============================================================================
# 4. Publication-Quality Visualizations
# ==============================================================================

class Visualizer:
    """Matplotlib styling and artifact export engine."""

    # Academic warm-palette theme configuration
    THEME = {
        "bg_color": "#FAF8F5",
        "card_bg": "#FFFFFF",
        "text_dark": "#1E293B",
        "text_muted": "#475569",
        "border_color": "#CBD5E1",
        "ruin_color": "#BE123C",     # Dusty Rose
        "win_color": "#047857",      # Sage Green
        "walk_blue": "#2563EB",      # Pastel / Classic Blue
        "accent_purple": "#6D28D9",  # Muted Lavender
        "accent_amber": "#B45309",   # Warm Amber
    }

    @classmethod
    def apply_academic_style(cls) -> None:
        """Apply clean typography, high DPI, and warm cream canvas styles."""
        plt.rcParams.update({
            "figure.facecolor": cls.THEME["bg_color"],
            "axes.facecolor": cls.THEME["card_bg"],
            "axes.edgecolor": cls.THEME["border_color"],
            "axes.labelcolor": cls.THEME["text_dark"],
            "text.color": cls.THEME["text_dark"],
            "xtick.color": cls.THEME["text_muted"],
            "ytick.color": cls.THEME["text_muted"],
            "grid.color": "#E2E8F0",
            "grid.linestyle": "--",
            "grid.alpha": 0.7,
            "font.family": "sans-serif",
            "font.size": 11,
            "figure.titlesize": 14,
            "figure.dpi": 300,
        })

    @classmethod
    def plot_sample_trajectories(
        cls,
        sample_paths: List[np.ndarray],
        s: int,
        N: int,
        p: float,
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """Plot multiple random walk trajectories showing absorption at 0 and N."""
        cls.apply_academic_style()
        fig, ax = plt.subplots(figsize=(10, 6))

        max_len = 0
        for path in sample_paths:
            max_len = max(max_len, len(path))
            final_pos = path[-1]
            color = cls.THEME["win_color"] if final_pos >= N else cls.THEME["ruin_color"]
            alpha = 0.55 if len(sample_paths) <= 30 else 0.35
            ax.plot(path, color=color, linewidth=1.3, alpha=alpha)

        # Plot boundary planes and initial capital
        ax.axhline(N, color=cls.THEME["win_color"], linestyle="--", linewidth=2.0,
                   label=f"Target Fortune N = {N} (Win)")
        ax.axhline(0, color=cls.THEME["ruin_color"], linestyle="-", linewidth=2.0,
                   label="Ruin Boundary 0 (Bankruptcy)")
        ax.axhline(s, color=cls.THEME["accent_amber"], linestyle=":", linewidth=1.8,
                   label=f"Initial Capital s = {s}")

        ax.set_title(
            f"Stochastic Random Walk Trajectories\n"
            f"(Initial Capital $s={s}$, Target $N={N}$, Step Probability $p={p:.2f}$)",
            fontweight="bold", pad=12
        )
        ax.set_xlabel("Discrete Time Step ($n$)")
        ax.set_ylabel("Gambler's Capital ($S_n$)")
        ax.set_ylim(-1, N + 1)
        ax.set_xlim(0, max_len + 2)
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True, facecolor=cls.THEME["bg_color"],
                  edgecolor=cls.THEME["border_color"])

        plt.tight_layout()
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300)
            print(f"[Plot Exported] {output_path}")
        if show:
            plt.show()
        plt.close()

    @classmethod
    def plot_ruin_probability_curves(
        cls,
        N: int = 20,
        p_values: Optional[List[float]] = None,
        num_trials: int = 3_000,
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        Plot theoretical closed-form ruin curves vs empirical Monte Carlo points
        across varying starting capital s and probabilities p.
        """
        if p_values is None:
            p_values = [0.45, 0.49, 0.50, 0.51, 0.55]

        cls.apply_academic_style()
        fig, ax = plt.subplots(figsize=(10, 6))

        palette = [
            cls.THEME["ruin_color"],
            "#EA580C",                  # Warm Orange
            cls.THEME["walk_blue"],
            cls.THEME["accent_purple"],
            cls.THEME["win_color"],
        ]

        smooth_s = np.linspace(0, N, 200)

        for idx, p in enumerate(p_values):
            col = palette[idx % len(palette)]
            # Theoretical curve
            theo_curve = [GamblersRuinTheory.ruin_probability(s_val, N, p) for s_val in smooth_s]
            ax.plot(smooth_s, theo_curve, color=col, linewidth=2.2,
                    label=f"Theory: $p={p:.2f}$")

            # Empirical points
            sweep = sweep_capital_range(N=N, p=p, num_trials=num_trials, seed=42 + idx)
            ax.scatter(sweep["capitals"], sweep["empirical_ruin"], color=col,
                       edgecolor="#0F172A", s=32, zorder=4, alpha=0.9,
                       label=f"Simulated ($M={num_trials}$)" if idx == 0 else None)

        ax.set_title(
            f"Probability of Ruin vs. Initial Capital ($N={N}$)\n"
            f"Theoretical Closed-Form vs. Empirical Monte Carlo Validation",
            fontweight="bold", pad=12
        )
        ax.set_xlabel("Initial Capital ($s$)")
        ax.set_ylabel("Probability of Ruin ($R_s$)")
        ax.set_xlim(0, N)
        ax.set_ylim(-0.02, 1.02)
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True, facecolor=cls.THEME["bg_color"],
                  edgecolor=cls.THEME["border_color"], fontsize=9)

        plt.tight_layout()
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300)
            print(f"[Plot Exported] {output_path}")
        if show:
            plt.show()
        plt.close()

    @classmethod
    def plot_expected_duration(
        cls,
        N: int = 20,
        p_values: Optional[List[float]] = None,
        num_trials: int = 3_000,
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """Plot parabolic and skewed expected stopping times E[T] vs initial capital s."""
        if p_values is None:
            p_values = [0.45, 0.50, 0.55]

        cls.apply_academic_style()
        fig, ax = plt.subplots(figsize=(10, 6))

        palette = [cls.THEME["ruin_color"], cls.THEME["walk_blue"], cls.THEME["win_color"]]
        smooth_s = np.linspace(0, N, 200)

        for idx, p in enumerate(p_values):
            col = palette[idx % len(palette)]
            theo_dur = [GamblersRuinTheory.expected_duration(s_val, N, p) for s_val in smooth_s]
            ax.plot(smooth_s, theo_dur, color=col, linewidth=2.2,
                    label=f"Theory: $p={p:.2f}$" + (" (Parabolic $s(N-s)$)" if np.isclose(p, 0.5) else ""))

            sweep = sweep_capital_range(N=N, p=p, num_trials=num_trials, seed=100 + idx)
            ax.scatter(sweep["capitals"], sweep["empirical_duration"], color=col,
                       edgecolor="#0F172A", s=34, zorder=4, alpha=0.9)

        ax.set_title(
            f"Expected Duration of Game $E[T]$ vs. Initial Capital ($N={N}$)\n"
            f"Stopping Time Characteristics under Varying Biases",
            fontweight="bold", pad=12
        )
        ax.set_xlabel("Initial Capital ($s$)")
        ax.set_ylabel("Expected Stopping Time $E[T]$ (Steps)")
        ax.set_xlim(0, N)
        ax.grid(True)
        ax.legend(loc="upper left", frameon=True, facecolor=cls.THEME["bg_color"],
                  edgecolor=cls.THEME["border_color"])

        plt.tight_layout()
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300)
            print(f"[Plot Exported] {output_path}")
        if show:
            plt.show()
        plt.close()

    @classmethod
    def plot_convergence(
        s: int,
        N: int,
        p: float,
        trial_steps: List[int],
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """Plot Monte Carlo estimation error decay as trial count increases."""
        Visualizer.apply_academic_style()
        fig, ax = plt.subplots(figsize=(10, 6))

        steps, errors, theo_val = evaluate_convergence(s, N, p, trial_steps)

        ax.plot(steps, errors, marker="o", color=Visualizer.THEME["walk_blue"],
                linewidth=2.0, label="Empirical Absolute Error $|\\hat{R} - R_{\\text{theo}}|$")

        # Theoretical CLT rate envelope O(1 / sqrt(M))
        c_rate = errors[0] * np.sqrt(steps[0])
        clt_bound = c_rate / np.sqrt(steps)
        ax.plot(steps, clt_bound, linestyle="--", color=Visualizer.THEME["ruin_color"],
                linewidth=1.8, label=r"CLT Rate Envelope $\mathcal{O}(1/\sqrt{M})$")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(
            f"Monte Carlo Convergence & Error Decay ($s={s}, N={N}, p={p:.2f}$)\n"
            f"Adherence to Central Limit Theorem and Law of Large Numbers",
            fontweight="bold", pad=12
        )
        ax.set_xlabel("Number of Simulation Trials $M$ (Log Scale)")
        ax.set_ylabel("Absolute Discrepancy (Log Scale)")
        ax.grid(True, which="both")
        ax.legend(loc="upper right", frameon=True, facecolor=Visualizer.THEME["bg_color"],
                  edgecolor=Visualizer.THEME["border_color"])

        plt.tight_layout()
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300)
            print(f"[Plot Exported] {output_path}")
        if show:
            plt.show()
        plt.close()


# ==============================================================================
# 5. CLI & Execution Entry Point
# ==============================================================================

def print_summary_table(res: SimulationResult) -> None:
    """Print a clean academic report of simulation and theoretical findings."""
    print("\n" + "=" * 70)
    print("      SIMPLE RANDOM WALK & GAMBLER'S RUIN: EXPERIMENTAL REPORT      ")
    print("=" * 70)
    print(f"  Initial Capital (s)       : {res.initial_capital}")
    print(f"  Target Capital (N)        : {res.target_capital}")
    print(f"  Step Win Probability (p)  : {res.win_probability:.4f} "
          f"({'Symmetric/Fair' if np.isclose(res.win_probability, 0.5) else 'Asymmetric/Biased'})")
    print(f"  Monte Carlo Trials (M)    : {res.num_trials:,}")
    print("-" * 70)
    print("  METRIC                     EMPIRICAL              THEORETICAL")
    print("-" * 70)
    print(f"  Ruin Probability (0)     : {res.empirical_ruin_prob:10.4f}             {res.theoretical_ruin_prob:10.4f}")
    print(f"  Win Probability  (N)     : {res.empirical_win_prob:10.4f}             {res.theoretical_win_prob:10.4f}")
    print(f"  Standard Error (SE)      : {res.standard_error:10.4f}                    N/A")
    print(f"  95% Confidence Interval  : [{res.confidence_interval_95[0]:.4f}, {res.confidence_interval_95[1]:.4f}]           N/A")
    print(f"  Expected Duration E[T]   : {res.empirical_mean_duration:10.2f} steps       {res.theoretical_mean_duration:10.2f} steps")
    print("-" * 70)

    abs_error = abs(res.empirical_ruin_prob - res.theoretical_ruin_prob)
    z_score = abs_error / res.standard_error if res.standard_error > 0 else 0.0
    print(f"  Absolute Discrepancy     : {abs_error:.6f}")
    print(f"  Statistical Z-Score      : {z_score:.2f} (Accepted if |Z| < 2.58 at 99% level)")
    print("=" * 70 + "\n")


def main() -> None:
    """Main CLI orchestrator supporting custom parameters and automatic plot exports."""
    parser = argparse.ArgumentParser(
        description="Monte Carlo Simulation & Theoretical Engine for Gambler's Ruin",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-s", "--capital", type=int, default=10, help="Initial gambler capital")
    parser.add_argument("-N", "--target", type=int, default=20, help="Target fortune (absorbing upper bound)")
    parser.add_argument("-p", "--prob", type=float, default=0.5, help="Single-step win probability")
    parser.add_argument("-m", "--trials", type=int, default=20_000, help="Number of Monte Carlo trials")
    parser.add_argument("--seed", type=int, default=42, help="Pseudorandom generator seed")
    parser.add_argument("--save-plots", action="store_true", default=True, help="Export high-resolution plots")
    parser.add_argument("--output-dir", type=str, default="assets/screenshots", help="Directory to save plots")
    parser.add_argument("--show", action="store_true", default=False, help="Display interactive GUI windows")

    args = parser.parse_args()

    # Input validation
    if not (0 < args.capital < args.target):
        sys.exit(f"Error: Initial capital s ({args.capital}) must satisfy 0 < s < N ({args.target}).")
    if not (0.0 < args.prob < 1.0):
        sys.exit(f"Error: Step probability p ({args.prob}) must lie in interval (0, 1).")

    # Run Monte Carlo Simulation
    engine = MonteCarloEngine(seed=args.seed)
    result = engine.run_simulation(
        s=args.capital,
        N=args.target,
        p=args.prob,
        num_trials=args.trials,
        max_sample_paths=40,
    )

    # Print Formatted Academic Table
    print_summary_table(result)

    # Generate Publication Plots
    if args.save_plots or args.show:
        out_dir = args.output_dir
        os.makedirs(out_dir, exist_ok=True)

        print("[Generating Visualizations] Please wait...")

        # Plot 1: Stochastic Trajectories
        Visualizer.plot_sample_trajectories(
            sample_paths=result.sample_paths,
            s=args.capital,
            N=args.target,
            p=args.prob,
            output_path=os.path.join(out_dir, "monte_carlo_trajectories.png"),
            show=args.show,
        )

        # Plot 2: Ruin Probability Curves vs Starting Capital
        Visualizer.plot_ruin_probability_curves(
            N=args.target,
            p_values=[0.45, 0.49, 0.50, 0.51, 0.55],
            num_trials=min(args.trials, 3_000),
            output_path=os.path.join(out_dir, "ruin_probability_curves.png"),
            show=args.show,
        )

        # Plot 3: Expected Duration Parabolic & Skewed Curves
        Visualizer.plot_expected_duration(
            N=args.target,
            p_values=[0.45, 0.50, 0.55],
            num_trials=min(args.trials, 3_000),
            output_path=os.path.join(out_dir, "expected_duration_curves.png"),
            show=args.show,
        )

        # Plot 4: Convergence Error Decay
        Visualizer.plot_convergence(
            s=args.capital,
            N=args.target,
            p=args.prob,
            trial_steps=[100, 500, 1_000, 5_000, 10_000, 25_000, 50_000],
            output_path=os.path.join(out_dir, "convergence_analysis.png"),
            show=args.show,
        )

        print(f"[Complete] All artifacts saved to directory: {os.path.abspath(out_dir)}")


if __name__ == "__main__":
    main()
