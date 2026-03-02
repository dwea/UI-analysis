"""
Generate static chart PNGs for the NovaPulse visualization website.
All charts use a clean light theme.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.colors as mcolors
import seaborn as sns
import os, warnings
warnings.filterwarnings("ignore")

# ── Style ─────────────────────────────────────────────────────────────────────

PHASE_COLORS = {
    "Phase A": "#4E79A7",
    "Phase B": "#F28E2B",
    "Phase C": "#E15759",
    "Phase D": "#76B7B2",
    "Phase E": "#59A14F",
    "Phase F": "#EDC948",
}
PHASE_ORDER = ["Phase A", "Phase B", "Phase C", "Phase D", "Phase E", "Phase F"]

EXP_COLORS = {
    "expert":  "#2166AC",
    "senior":  "#74ADD1",
    "mid":     "#F4A582",
    "novice":  "#D6604D",
}

def setup_style():
    plt.rcParams.update({
        "figure.facecolor":  "white",
        "axes.facecolor":    "#F9F9F9",
        "axes.edgecolor":    "#CCCCCC",
        "axes.grid":         True,
        "grid.color":        "#E5E5E5",
        "grid.linestyle":    "-",
        "grid.linewidth":    0.7,
        "font.family":       "DejaVu Sans",
        "font.size":         11,
        "axes.titlesize":    14,
        "axes.titleweight":  "bold",
        "axes.labelsize":    12,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "legend.framealpha": 0.9,
        "legend.edgecolor":  "#CCCCCC",
    })

setup_style()

# ── Load data ─────────────────────────────────────────────────────────────────

df       = pd.read_csv("data/event_log.csv", parse_dates=["timestamp"])
trans    = pd.read_csv("data/transitions.csv")
phase_s  = pd.read_csv("data/phase_summary.csv")
elem_f   = pd.read_csv("data/element_frequency.csv")
dfg_e    = pd.read_csv("data/dfg_edges.csv")

os.makedirs("charts", exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DOTTED CHART  (case × time, coloured by phase)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_dotted():
    fig, ax = plt.subplots(figsize=(14, 8))

    cases = df["case_id"].unique()
    case_idx = {c: i for i, c in enumerate(cases)}

    for phase in PHASE_ORDER:
        sub = df[df["phase"] == phase]
        y = [case_idx[c] for c in sub["case_id"]]
        # Normalise timestamp to minutes from procedure start
        starts = df.groupby("case_id")["timestamp"].min()
        x = [(sub.iloc[j]["timestamp"] - starts[sub.iloc[j]["case_id"]]).total_seconds() / 60
             for j in range(len(sub))]
        ax.scatter(x, y, c=PHASE_COLORS[phase], s=8, alpha=0.55, label=phase, linewidths=0)

    ax.set_xlabel("Time from Procedure Start (minutes)")
    ax.set_ylabel("Procedure (case)")
    ax.set_title("Dotted Chart — All Interactions Across All Procedures")
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([f"#{i+1}" for i in range(len(cases))], fontsize=7)
    ax.legend(title="Phase", loc="upper right", markerscale=3, fontsize=9)
    fig.tight_layout()
    fig.savefig("charts/dotted_chart.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ dotted_chart.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. DIRECTLY-FOLLOWS GRAPH  (top-N edges, drawn with arrows)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_dfg():
    # Use phase-level DFG for clarity
    phase_trans = trans.groupby(["phase_from", "phase_to"]).size().reset_index(name="freq")
    phase_trans = phase_trans[phase_trans["phase_from"] != phase_trans["phase_to"]]

    # Layout: phases in a rough left-to-right arc
    positions = {
        "Phase A": (0.1, 0.5),
        "Phase B": (0.28, 0.75),
        "Phase C": (0.5, 0.88),
        "Phase D": (0.72, 0.75),
        "Phase E": (0.85, 0.45),
        "Phase F": (0.65, 0.18),
    }

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("white"); fig.patch.set_facecolor("white")

    max_freq = phase_trans["freq"].max()

    for _, row in phase_trans.iterrows():
        src = positions.get(row["phase_from"])
        dst = positions.get(row["phase_to"])
        if not src or not dst:
            continue
        w = 0.5 + 4.5 * (row["freq"] / max_freq)
        alpha = 0.3 + 0.65 * (row["freq"] / max_freq)
        ax.annotate("", xy=dst, xytext=src,
                    arrowprops=dict(arrowstyle="-|>", lw=w,
                                   color="#555555", alpha=alpha,
                                   connectionstyle="arc3,rad=0.08"))
        mx, my = (src[0]+dst[0])/2, (src[1]+dst[1])/2
        ax.text(mx, my, str(int(row["freq"])), ha="center", va="center",
                fontsize=8, color="#333333",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))

    for phase, (x, y) in positions.items():
        n_events = len(df[df["phase"] == phase])
        ax.scatter([x], [y], s=1800, c=[PHASE_COLORS[phase]], zorder=5,
                   edgecolors="white", linewidths=2)
        ax.text(x, y+0.005, phase, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white", zorder=6)
        ax.text(x, y-0.085, f"{n_events:,} events", ha="center", va="top",
                fontsize=8, color="#555555")

    ax.set_title("Directly-Follows Graph — Phase-Level Workflow", pad=15, fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig("charts/dfg.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ dfg.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. SANKEY  (phase transitions — approximated with stacked flow bars)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_sankey():
    """Sankey-style alluvial using matplotlib band polygons."""
    # Procedure-level phase sequence
    phase_counts = df.groupby(["case_id", "phase"])["ui_element"].count().reset_index()
    phase_counts.columns = ["case_id", "phase", "n"]

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.axis("off")
    fig.patch.set_facecolor("white")

    n_phases = len(PHASE_ORDER)
    col_x = np.linspace(0.05, 0.95, n_phases)
    node_width = 0.04

    # Aggregate n per phase
    phase_totals = {p: phase_counts[phase_counts["phase"] == p]["n"].sum() for p in PHASE_ORDER}
    grand_total = max(phase_totals.values())

    bar_height = 0.7
    node_heights = {p: bar_height * phase_totals[p] / grand_total for p in PHASE_ORDER}
    node_bottoms = {p: (bar_height - node_heights[p]) / 2 for p in PHASE_ORDER}

    # Draw nodes
    for i, phase in enumerate(PHASE_ORDER):
        x = col_x[i] - node_width / 2
        h = node_heights[phase]
        b = node_bottoms[phase]
        rect = plt.Rectangle((x, b), node_width, h,
                              facecolor=PHASE_COLORS[phase], edgecolor="white", lw=1.5, zorder=5)
        ax.add_patch(rect)
        ax.text(col_x[i], b + h + 0.04, phase, ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=PHASE_COLORS[phase])
        ax.text(col_x[i], b - 0.04, f"{phase_totals[phase]:,}", ha="center", va="top",
                fontsize=8, color="#555555")

    # Draw flow bands between consecutive phases
    for i in range(n_phases - 1):
        p1, p2 = PHASE_ORDER[i], PHASE_ORDER[i+1]
        # overlap = cases that have both phases
        both = phase_counts[phase_counts["phase"].isin([p1, p2])]
        both_cases = both.groupby("case_id")["phase"].nunique()
        n_both = (both_cases == 2).sum()

        x1 = col_x[i]   + node_width / 2
        x2 = col_x[i+1] - node_width / 2

        h1 = node_heights[p1] * 0.7
        h2 = node_heights[p2] * 0.7
        b1 = node_bottoms[p1] + (node_heights[p1] - h1) / 2
        b2 = node_bottoms[p2] + (node_heights[p2] - h2) / 2

        # Cubic bezier polygon
        t = np.linspace(0, 1, 60)
        cx = 0.5
        top1 = b1 + h1
        top2 = b2 + h2
        # top edge
        xt = x1 + (x2 - x1) * t
        yt_top = top1 + (top2 - top1) * (3*t**2 - 2*t**3)
        yt_bot = b1   + (b2   - b1)   * (3*t**2 - 2*t**3)

        verts_x = list(xt) + list(xt[::-1])
        verts_y = list(yt_top) + list(yt_bot[::-1])

        color = PHASE_COLORS[p1]
        poly = plt.Polygon(list(zip(verts_x, verts_y)),
                           facecolor=color, alpha=0.28, edgecolor="none", zorder=2)
        ax.add_patch(poly)

    ax.set_xlim(0, 1); ax.set_ylim(-0.12, 0.95)
    ax.set_title("Sankey Flow Diagram — Procedure Volume Through Phases", fontsize=14, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig("charts/sankey.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ sankey.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. HEATMAP  (UI element × phase interaction density)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_heatmap():
    pivot = elem_f.pivot_table(index="ui_element", columns="phase", values="count", fill_value=0)
    # Reorder columns
    pivot = pivot[[p for p in PHASE_ORDER if p in pivot.columns]]
    # Sort rows by total
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(11, 10))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", linewidths=0.4, linecolor="#EEEEEE",
                annot=True, fmt=".0f", annot_kws={"size": 8},
                cbar_kws={"label": "Total Interactions", "shrink": 0.7})
    ax.grid(False)
    ax.set_title("Interaction Heatmap — UI Element × Phase", pad=12)
    ax.set_xlabel("Phase")
    ax.set_ylabel("UI Element")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    fig.savefig("charts/heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ heatmap.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. VARIANT COMPARISON  (phase duration by experience level — violin + strip)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_variants():
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharey=False)
    axes = axes.flatten()
    exp_order = ["expert", "senior", "mid", "novice"]

    for i, phase in enumerate(PHASE_ORDER):
        ax = axes[i]
        sub = phase_s[phase_s["phase"] == phase].copy()
        sub["duration_min"] = sub["phase_duration_s"] / 60

        vp = ax.violinplot(
            [sub[sub["experience_level"] == e]["duration_min"].values for e in exp_order],
            positions=range(len(exp_order)), widths=0.6, showmedians=True
        )
        for j, body in enumerate(vp["bodies"]):
            body.set_facecolor(list(EXP_COLORS.values())[j])
            body.set_alpha(0.55)
        vp["cmedians"].set_color("#222222")
        vp["cmedians"].set_linewidth(2)
        for part in ["cbars", "cmins", "cmaxes"]:
            vp[part].set_color("#888888")

        # Strip overlay
        for j, exp in enumerate(exp_order):
            ys = sub[sub["experience_level"] == exp]["duration_min"].values
            xs = np.random.normal(j, 0.07, len(ys))
            ax.scatter(xs, ys, c=EXP_COLORS[exp], s=18, alpha=0.7, zorder=5)

        ax.set_xticks(range(len(exp_order)))
        ax.set_xticklabels(exp_order, fontsize=9, rotation=15)
        ax.set_title(phase, fontweight="bold")
        ax.set_ylabel("Duration (min)" if i % 3 == 0 else "")

    patches = [mpatches.Patch(color=c, label=e) for e, c in EXP_COLORS.items()]
    fig.legend(handles=patches, title="Experience", loc="lower center",
               ncol=4, bbox_to_anchor=(0.5, -0.02), frameon=True)
    fig.suptitle("Variant Comparison — Phase Duration by Operator Experience", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig("charts/variants.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ variants.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. PHASE-ALIGNED TIMELINE  (Gantt-style, sorted by total duration)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_timeline():
    # Aggregate phase start/end per case
    phase_times = df.groupby(["case_id", "phase"]).agg(
        start=("timestamp", "min"),
        end=("timestamp", "max")
    ).reset_index()

    # Align to procedure start = 0
    proc_starts = df.groupby("case_id")["timestamp"].min()
    phase_times["start_min"] = phase_times.apply(
        lambda r: (r["start"] - proc_starts[r["case_id"]]).total_seconds() / 60, axis=1)
    phase_times["dur_min"] = phase_times.apply(
        lambda r: max(0.5, (r["end"] - r["start"]).total_seconds() / 60), axis=1)

    # Sort cases by total duration
    total_dur = phase_times.groupby("case_id")["dur_min"].sum().sort_values()
    cases_sorted = total_dur.index.tolist()

    fig, ax = plt.subplots(figsize=(14, 9))

    for yi, case_id in enumerate(cases_sorted):
        sub = phase_times[phase_times["case_id"] == case_id]
        for _, row in sub.iterrows():
            ax.barh(yi, row["dur_min"], left=row["start_min"],
                    height=0.75, color=PHASE_COLORS.get(row["phase"], "#AAAAAA"),
                    edgecolor="white", linewidth=0.4, alpha=0.88)

    ax.set_yticks(range(len(cases_sorted)))
    ax.set_yticklabels([f"#{i+1}" for i in range(len(cases_sorted))], fontsize=7)
    ax.set_xlabel("Time from Procedure Start (minutes)")
    ax.set_ylabel("Procedure (sorted by total duration)")
    ax.set_title("Phase-Aligned Timeline — Gantt View of All Procedures")

    patches = [mpatches.Patch(color=PHASE_COLORS[p], label=p) for p in PHASE_ORDER]
    ax.legend(handles=patches, title="Phase", loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig("charts/timeline.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ timeline.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. DWELL TIME DISTRIBUTION (per phase, ridge-style)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_dwell():
    from scipy.stats import gaussian_kde

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_facecolor("white")

    offset = 0
    phase_offsets = {}
    for phase in reversed(PHASE_ORDER):
        vals = df[df["phase"] == phase]["dwell_time_s"].values
        vals = vals[vals < np.percentile(vals, 97)]  # clip outliers
        kde = gaussian_kde(vals, bw_method=0.25)
        x = np.linspace(0, vals.max(), 300)
        y = kde(x)
        y = y / y.max() * 0.9  # normalise height

        ax.fill_between(x, offset, offset + y,
                        color=PHASE_COLORS[phase], alpha=0.6)
        ax.plot(x, offset + y, color=PHASE_COLORS[phase], lw=1.5)
        ax.axhline(offset, color="#CCCCCC", lw=0.7)
        ax.text(-0.6, offset + 0.3, phase, ha="right", va="center",
                fontsize=10, fontweight="bold", color=PHASE_COLORS[phase])
        phase_offsets[phase] = offset
        offset += 1.0

    ax.set_xlim(-0.3, 20)
    ax.set_xlabel("Dwell Time per Interaction (seconds)")
    ax.set_yticks([])
    ax.set_title("Dwell Time Distribution — Ridge Plot by Phase")
    ax.spines[["left", "top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("charts/dwell_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ dwell_distribution.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. TRANSITION MATRIX HEATMAP  (phase-to-phase)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_transition_matrix():
    mat = trans.groupby(["phase_from", "phase_to"]).size().reset_index(name="count")
    pivot = mat.pivot_table(index="phase_from", columns="phase_to", values="count", fill_value=0)
    pivot = pivot.reindex(index=PHASE_ORDER, columns=PHASE_ORDER, fill_value=0)

    # Normalise rows → probability
    pivot_norm = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(pivot_norm, ax=ax, cmap="Blues", annot=True, fmt=".2f",
                linewidths=0.5, linecolor="#EEEEEE",
                cbar_kws={"label": "Transition Probability"})
    ax.grid(False)
    ax.set_title("Phase Transition Probability Matrix")
    ax.set_xlabel("To Phase")
    ax.set_ylabel("From Phase")
    ax.tick_params(axis="both", rotation=0)
    fig.tight_layout()
    fig.savefig("charts/transition_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ transition_matrix.png")

# ═══════════════════════════════════════════════════════════════════════════════
# Run all
# ═══════════════════════════════════════════════════════════════════════════════

print("Generating charts...")
chart_dotted()
chart_dfg()
chart_sankey()
chart_heatmap()
chart_variants()
chart_timeline()
chart_dwell()
chart_transition_matrix()
print("\nAll charts generated in ./charts/")
