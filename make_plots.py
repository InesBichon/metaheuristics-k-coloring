"""
Generate comparison plots for the three approaches:
  - initial greedy heuristic   (result_initial_coloring.txt)
  - classic descent            (output_descent/best_*.txt)
  - simulated annealing + GRASP (output_exam/best_*.txt)

Produces three PNGs in plots/.
"""
import os
import re
import matplotlib.pyplot as plt

# ---- Okabe-Ito colorblind-safe palette (fixed order, consistent across plots) ----
C_INITIAL = "#E69F00"   # orange  -> initial greedy
C_DESCENT = "#0072B2"   # blue    -> descent
C_SA      = "#009E73"   # green   -> SA + GRASP
C_TTOTAL  = "#0072B2"   # dark blue  -> full run time
C_TBEST   = "#56B4E9"   # light blue -> time to best (a portion of the full run)

INK = "#222222"
MUTED = "#888888"


def parse_initial(path="result_initial_coloring.txt"):
    out = {}
    with open(path) as f:
        next(f)  # header
        for line in f:
            line = line.strip()
            if not line:
                continue
            name, conflicts = line.split("\t")
            name = os.path.splitext(os.path.basename(name))[0]
            out[name] = int(conflicts)
    return out


def parse_best_dir(directory):
    """Return {graph: {conflicts, run_total_time, time_to_best}} from best_*.txt."""
    out = {}
    for fn in os.listdir(directory):
        if not (fn.startswith("best_") and fn.endswith(".txt")):
            continue
        name = fn[len("best_"):-len(".txt")]
        d = {}
        with open(os.path.join(directory, fn)) as f:
            for line in f:
                if line.startswith("best_nb_of_conflicts"):
                    d["conflicts"] = int(line.split("=", 1)[1])
                elif line.startswith("run_total_time_seconds"):
                    d["run_total_time"] = float(line.split("=", 1)[1])
                elif line.startswith("time_to_best_within_run_seconds"):
                    d["time_to_best"] = float(line.split("=", 1)[1])
        out[name] = d
    return out


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK)
    ax.yaxis.grid(True, color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    os.makedirs("plots", exist_ok=True)
    initial = parse_initial()
    descent = parse_best_dir("output_descent")
    sa = parse_best_dir("output_exam")

    # Common graph order: sorted by initial conflicts, descending (readable backbone)
    graphs = sorted(initial, key=lambda g: initial[g], reverse=True)
    x = range(len(graphs))

    # ---------- PLOT 1: three conflict values per graph (points, log scale) ----------
    init_v = [initial[g] for g in graphs]
    desc_v = [descent[g]["conflicts"] for g in graphs]
    sa_v = [sa[g]["conflicts"] for g in graphs]

    fig, ax = plt.subplots(figsize=(15, 6.5))
    # thin connector showing the drop from initial -> best, per graph
    for xi, iv, dv, sv in zip(x, init_v, desc_v, sa_v):
        lo, hi = min(iv, dv, sv), max(iv, dv, sv)
        ax.plot([xi, xi], [lo, hi], color="#CCCCCC", linewidth=1.0, zorder=1)
    ax.scatter(x, init_v, s=55, color=C_INITIAL, label="Initial greedy", zorder=3, edgecolor="white", linewidth=0.5)
    ax.scatter(x, desc_v, s=55, color=C_DESCENT, label="Descent", marker="s", zorder=3, edgecolor="white", linewidth=0.5)
    ax.scatter(x, sa_v, s=55, color=C_SA, label="SA + GRASP", marker="D", zorder=4, edgecolor="white", linewidth=0.5)
    # symlog so that 0-conflict (solved) results are still shown, at the bottom
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(bottom=-0.3)
    # label the solved (0-conflict) points so they are not mistaken for missing data
    for xi, dv, sv in zip(x, desc_v, sa_v):
        if sv == 0:
            ax.annotate("0", (xi, 0), xytext=(2, 6), textcoords="offset points", color=C_SA, fontsize=8, fontweight="bold")
        elif dv == 0:
            ax.annotate("0", (xi, 0), xytext=(2, 6), textcoords="offset points", color=C_DESCENT, fontsize=8, fontweight="bold")
    ax.set_ylabel("Number of conflicts (symlog scale)", color=INK)
    ax.set_title("Conflicts per graph: initial greedy vs descent vs SA + GRASP", color=INK, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(graphs, rotation=90, fontsize=8)
    style_axes(ax)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("plots/1_conflicts_comparison.png", dpi=150)
    plt.close(fig)

    # ---------- PLOT 1b: same as plot 1 but with a linear y-axis ----------
    fig, ax = plt.subplots(figsize=(15, 6.5))
    for xi, iv, dv, sv in zip(x, init_v, desc_v, sa_v):
        lo, hi = min(iv, dv, sv), max(iv, dv, sv)
        ax.plot([xi, xi], [lo, hi], color="#CCCCCC", linewidth=1.0, zorder=1)
    ax.scatter(x, init_v, s=55, color=C_INITIAL, label="Initial greedy", zorder=3, edgecolor="white", linewidth=0.5)
    ax.scatter(x, desc_v, s=55, color=C_DESCENT, label="Descent", marker="s", zorder=3, edgecolor="white", linewidth=0.5)
    ax.scatter(x, sa_v, s=55, color=C_SA, label="SA + GRASP", marker="D", zorder=4, edgecolor="white", linewidth=0.5)
    ax.set_ylabel("Number of conflicts (linear scale)", color=INK)
    ax.set_title("Conflicts per graph: initial greedy vs descent vs SA + GRASP (linear scale)", color=INK, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(graphs, rotation=90, fontsize=8)
    style_axes(ax)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("plots/1b_conflicts_comparison_linear.png", dpi=150)
    plt.close(fig)

    # ---------- PLOT 2: SA+GRASP run_total_time vs time_to_best (grouped bars) ----------
    total_t = [sa[g]["run_total_time"] for g in graphs]
    best_t = [sa[g]["time_to_best"] for g in graphs]

    fig, ax = plt.subplots(figsize=(15, 6.5))
    w = 0.4
    ax.bar([xi - w / 2 for xi in x], total_t, width=w, color=C_TTOTAL, label="Run total time")
    ax.bar([xi + w / 2 for xi in x], best_t, width=w, color=C_TBEST, label="Time to best")
    ax.set_yscale("log")
    ax.set_ylabel("Seconds per run (log scale)", color=INK)
    ax.set_title(
        "SA + GRASP: time of a full run vs time to reach its best\n"
        "(time-to-best close to the full run time => the best keeps improving at the end "
        "=> more iterations would help)",
        color=INK, fontweight="bold", fontsize=11,
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(graphs, rotation=90, fontsize=8)
    style_axes(ax)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("plots/2_sa_times.png", dpi=150)
    plt.close(fig)

    # ---------- PLOT 3: relative improvement over greedy (%) ----------
    def improvement(best):
        return [100.0 * (initial[g] - best[g]["conflicts"]) / initial[g] if initial[g] else 0.0
                for g in graphs]

    desc_imp = improvement(descent)
    sa_imp = improvement(sa)

    fig, ax = plt.subplots(figsize=(15, 6.5))
    w = 0.4
    ax.bar([xi - w / 2 for xi in x], desc_imp, width=w, color=C_DESCENT, label="Descent")
    ax.bar([xi + w / 2 for xi in x], sa_imp, width=w, color=C_SA, label="SA + GRASP")
    ax.set_ylabel("Conflicts reduced vs initial greedy (%)", color=INK)
    ax.set_title("How much each local search improves on the initial greedy coloring", color=INK, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(graphs, rotation=90, fontsize=8)
    style_axes(ax)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("plots/3_improvement_over_greedy.png", dpi=150)
    plt.close(fig)

    # ---- quick sanity table to stdout ----
    print(f"{'graph':<22}{'initial':>9}{'descent':>9}{'SA':>8}{'tot_t':>9}{'best_t':>9}{'t_b/tot':>9}")
    for g in graphs:
        tt, tb = sa[g]["run_total_time"], sa[g]["time_to_best"]
        print(f"{g:<22}{initial[g]:>9}{descent[g]['conflicts']:>9}{sa[g]['conflicts']:>8}"
              f"{tt:>9.2f}{tb:>9.2f}{(tb/tt if tt else 0):>9.2f}")
    print("\nSaved: plots/1_conflicts_comparison.png, plots/2_sa_times.png, plots/3_improvement_over_greedy.png")


if __name__ == "__main__":
    main()
