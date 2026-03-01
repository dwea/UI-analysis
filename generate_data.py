"""
Generate synthetic UI interaction log data for surgical workflow analysis.
Company: NovaPulse Medical Systems
"""

import pandas as pd
import numpy as np
import json
import os

np.random.seed(42)

# ── Configuration ────────────────────────────────────────────────────────────

PHASES = {
    "A": {"name": "Phase A", "label": "Phase A", "duration_mean": 180, "duration_std": 40},
    "B": {"name": "Phase B", "label": "Phase B", "duration_mean": 420, "duration_std": 90},
    "C": {"name": "Phase C", "label": "Phase C", "duration_mean": 360, "duration_std": 75},
    "D": {"name": "Phase D", "label": "Phase D", "duration_mean": 540, "duration_std": 120},
    "E": {"name": "Phase E", "label": "Phase E", "duration_mean": 240, "duration_std": 60},
    "F": {"name": "Phase F", "label": "Phase F", "duration_mean": 300, "duration_std": 80},
}

PHASE_ORDER = list(PHASES.keys())

# UI elements per phase — simulates real software screens
PHASE_UI_ELEMENTS = {
    "A": [
        "PatientDemographics.Load", "PatientDemographics.Confirm",
        "ProcedureSetup.SelectProtocol", "ProcedureSetup.ConfirmProtocol",
        "SystemCheck.RunDiagnostics", "SystemCheck.Confirm",
        "CatheterConfig.SelectType", "CatheterConfig.Confirm",
    ],
    "B": [
        "ImagingPanel.Zoom", "ImagingPanel.Pan", "ImagingPanel.Rotate",
        "ImagingPanel.Contrast", "ImagingPanel.ToggleOverlay",
        "AnatomyMap.SelectRegion", "AnatomyMap.MarkPoint", "AnatomyMap.ClearMark",
        "Navigation.ForwardStep", "Navigation.BackStep",
        "SegmentationTool.Draw", "SegmentationTool.Erase",
    ],
    "C": [
        "EnergyControl.SetPower", "EnergyControl.SetDuration",
        "EnergyControl.DeliverEnergy", "EnergyControl.Abort",
        "ContactSensor.CheckForce", "ContactSensor.Confirm",
        "LesionMap.MarkLesion", "LesionMap.ReviewLesion",
        "WaveformViewer.Pause", "WaveformViewer.Resume",
    ],
    "D": [
        "EnergyControl.SetPower", "EnergyControl.SetDuration",
        "EnergyControl.DeliverEnergy",
        "LesionMap.MarkLesion", "LesionMap.ReviewLesion",
        "LesionMap.DeleteLesion",
        "OutcomeTracker.RecordResult", "OutcomeTracker.FlagAnomaly",
        "WaveformViewer.Zoom", "WaveformViewer.SelectChannel",
        "ContactSensor.CheckForce",
    ],
    "E": [
        "ValidationPanel.RunCheck", "ValidationPanel.ReviewResult",
        "LesionMap.FinalReview", "LesionMap.ConfirmComplete",
        "OutcomeTracker.Summary", "OutcomeTracker.ExportData",
        "WaveformViewer.FinalCapture",
    ],
    "F": [
        "ReportGenerator.OpenTemplate", "ReportGenerator.FillFields",
        "ReportGenerator.Preview", "ReportGenerator.Export",
        "PatientRecord.Save", "PatientRecord.Close",
        "SystemCheck.Shutdown",
    ],
}

OPERATOR_PROFILES = {
    "OP_001": {"experience": "expert",   "avg_speed": 0.8},
    "OP_002": {"experience": "expert",   "avg_speed": 0.85},
    "OP_003": {"experience": "senior",   "avg_speed": 1.0},
    "OP_004": {"experience": "senior",   "avg_speed": 1.05},
    "OP_005": {"experience": "mid",      "avg_speed": 1.2},
    "OP_006": {"experience": "mid",      "avg_speed": 1.25},
    "OP_007": {"experience": "novice",   "avg_speed": 1.5},
    "OP_008": {"experience": "novice",   "avg_speed": 1.6},
}

# ── Generators ───────────────────────────────────────────────────────────────

def generate_procedure(proc_id, operator_id, start_time):
    """Generate a single synthetic procedure event log."""
    op = OPERATOR_PROFILES[operator_id]
    speed = op["avg_speed"] * np.random.normal(1.0, 0.1)

    events = []
    t = start_time

    for phase_key in PHASE_ORDER:
        phase = PHASES[phase_key]
        elements = PHASE_UI_ELEMENTS[phase_key]
        phase_duration = max(60, np.random.normal(phase["duration_mean"], phase["duration_std"]) * speed)

        n_interactions = int(phase_duration / 8 * np.random.normal(1.0, 0.15))
        n_interactions = max(5, n_interactions)

        # Weight toward earlier elements in each phase (natural workflow)
        weights = np.exp(-np.linspace(0, 1.5, len(elements)))
        weights = weights / weights.sum()

        interaction_times = sorted(np.random.uniform(0, phase_duration, n_interactions))

        prev_element = None
        for dt in interaction_times:
            element = np.random.choice(elements, p=weights)

            # Occasionally revisit previous element (backtracking)
            if prev_element and np.random.random() < 0.08:
                element = prev_element

            dwell = max(0.3, np.random.exponential(3.5) * speed)

            events.append({
                "case_id":         proc_id,
                "operator_id":     operator_id,
                "experience_level":op["experience"],
                "timestamp":       pd.Timestamp(t + pd.Timedelta(seconds=dt)),
                "phase":           phase["label"],
                "phase_key":       phase_key,
                "ui_element":      element,
                "screen":          element.split(".")[0],
                "action":          element.split(".")[1],
                "dwell_time_s":    round(dwell, 2),
                "phase_duration_s":round(phase_duration, 1),
            })
            prev_element = element

        t += pd.Timedelta(seconds=phase_duration + np.random.uniform(5, 30))

    return pd.DataFrame(events)


def generate_all_procedures(n=40):
    """Generate n procedures across all operators."""
    all_dfs = []
    operators = list(OPERATOR_PROFILES.keys())
    base_date = pd.Timestamp("2024-01-15 08:00:00")

    for i in range(n):
        proc_id = f"PROC_{i+1:04d}"
        operator = operators[i % len(operators)]
        # Spread over ~3 months
        start = base_date + pd.Timedelta(days=i * 2.1, hours=np.random.uniform(0, 8))
        df = generate_procedure(proc_id, operator, start)
        all_dfs.append(df)

    return pd.concat(all_dfs, ignore_index=True)


# ── Derived analytical datasets ───────────────────────────────────────────────

def compute_transition_matrix(df):
    """Compute UI element transition frequencies."""
    transitions = []
    for case_id, grp in df.groupby("case_id"):
        grp = grp.sort_values("timestamp")
        for i in range(len(grp) - 1):
            transitions.append({
                "from": grp.iloc[i]["ui_element"],
                "to":   grp.iloc[i+1]["ui_element"],
                "phase_from": grp.iloc[i]["phase"],
                "phase_to":   grp.iloc[i+1]["phase"],
            })
    return pd.DataFrame(transitions)


def compute_phase_summary(df):
    """Per-case phase timing summary."""
    rows = []
    for (case_id, phase), grp in df.groupby(["case_id", "phase"]):
        op = grp["operator_id"].iloc[0]
        rows.append({
            "case_id":          case_id,
            "operator_id":      op,
            "experience_level": grp["experience_level"].iloc[0],
            "phase":            phase,
            "phase_key":        grp["phase_key"].iloc[0],
            "n_interactions":   len(grp),
            "phase_duration_s": grp["phase_duration_s"].iloc[0],
            "mean_dwell_s":     grp["dwell_time_s"].mean(),
            "total_dwell_s":    grp["dwell_time_s"].sum(),
            "start_time":       grp["timestamp"].min(),
            "end_time":         grp["timestamp"].max(),
        })
    return pd.DataFrame(rows)


def compute_element_frequency(df):
    """Frequency and dwell stats per UI element."""
    stats = df.groupby(["phase", "ui_element"]).agg(
        count=("ui_element", "count"),
        mean_dwell=("dwell_time_s", "mean"),
        median_dwell=("dwell_time_s", "median"),
        total_dwell=("dwell_time_s", "sum"),
    ).reset_index()
    return stats


def compute_dfg_edges(df):
    """Directly-follows graph edge weights."""
    trans = compute_transition_matrix(df)
    dfg = trans.groupby(["from", "to"]).size().reset_index(name="frequency")
    dfg = dfg[dfg["from"] != dfg["to"]]  # remove self-loops for clarity
    dfg = dfg.sort_values("frequency", ascending=False)
    return dfg


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out_dir = "data"
    os.makedirs(out_dir, exist_ok=True)

    print("Generating procedures...")
    df = generate_all_procedures(n=40)
    df.to_csv(f"{out_dir}/event_log.csv", index=False)
    print(f"  event_log.csv  — {len(df):,} events across {df['case_id'].nunique()} procedures")

    print("Computing transitions...")
    trans = compute_transition_matrix(df)
    trans.to_csv(f"{out_dir}/transitions.csv", index=False)

    print("Computing phase summary...")
    phase_sum = compute_phase_summary(df)
    phase_sum.to_csv(f"{out_dir}/phase_summary.csv", index=False)

    print("Computing element frequency...")
    elem_freq = compute_element_frequency(df)
    elem_freq.to_csv(f"{out_dir}/element_frequency.csv", index=False)

    print("Computing DFG edges...")
    dfg = compute_dfg_edges(df)
    dfg.to_csv(f"{out_dir}/dfg_edges.csv", index=False)

    # Metadata for website
    meta = {
        "company": "NovaPulse Medical Systems",
        "product": "PulseNav Workflow Suite",
        "n_procedures": int(df["case_id"].nunique()),
        "n_events": len(df),
        "n_operators": int(df["operator_id"].nunique()),
        "phases": [{"key": k, "label": v["label"]} for k, v in PHASES.items()],
        "operators": [{"id": k, "experience": v["experience"]} for k, v in OPERATOR_PROFILES.items()],
        "date_range": [str(df["timestamp"].min()), str(df["timestamp"].max())],
    }
    with open(f"{out_dir}/metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print("\nDone. Files written to ./data/")
