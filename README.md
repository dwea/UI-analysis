# NovaPulse Medical Systems — PulseNav Workflow Analytics

## Project Overview

A static website showcasing 8 surgical UI workflow data visualizations for the
PulseNav Workflow Suite. All data is synthetic (generated procedurally) and safe
to use for demonstration, development, and testing.

---

## Directory Structure

```
.
├── README.md                  ← This file
├── generate_data.py           ← Python script: generates all CSV/JSON datasets
├── generate_charts.py         ← Python script: generates all PNG chart images
│
├── data/                      ← Generated datasets (CSVs + metadata JSON)
│   ├── event_log.csv          ← Master event log: 11,339 UI interactions × 40 procedures
│   ├── transitions.csv        ← All pairwise UI element transitions
│   ├── phase_summary.csv      ← Per-case, per-phase timing and interaction summary
│   ├── element_frequency.csv  ← UI element interaction counts and dwell stats by phase
│   ├── dfg_edges.csv          ← Directly-follows graph edge list with frequencies
│   └── metadata.json          ← Dataset metadata (n_procedures, phases, operators, etc.)
│
├── charts/                    ← Static PNG chart images (150 DPI)
│   ├── dotted_chart.png       ← Temporal scatter of all interactions by phase
│   ├── dfg.png                ← Directly-Follows Graph (phase-level)
│   ├── sankey.png             ← Sankey flow diagram (phase volumes)
│   ├── heatmap.png            ← UI element × phase interaction heatmap
│   ├── variants.png           ← Phase duration by operator experience (violin plots)
│   ├── timeline.png           ← Gantt-style phase-aligned timeline
│   ├── dwell_distribution.png ← Dwell time ridge plot by phase
│   └── transition_matrix.png  ← Phase-to-phase transition probability matrix
│
└── website/
    └── index.html             ← Tabbed single-page website (pure HTML/CSS/JS)
```

---

## Data Schema

### event_log.csv (master dataset)
| Column | Type | Description |
|---|---|---|
| case_id | string | Unique procedure identifier (PROC_0001 … PROC_0040) |
| operator_id | string | Operator identifier (OP_001 … OP_008) |
| experience_level | string | expert / senior / mid / novice |
| timestamp | datetime | UTC timestamp of interaction |
| phase | string | Phase A … Phase F |
| phase_key | string | A … F |
| ui_element | string | Screen.Action (e.g. EnergyControl.DeliverEnergy) |
| screen | string | UI screen component name |
| action | string | Specific action on that screen |
| dwell_time_s | float | Seconds spent on this interaction |
| phase_duration_s | float | Total duration of this phase for this case |

### Phases
| Phase | Procedural Role |
|---|---|
| Phase A | Setup & patient configuration |
| Phase B | Imaging & anatomy mapping |
| Phase C | Pre-treatment preparation |
| Phase D | Primary treatment delivery |
| Phase E | Validation & outcome review |
| Phase F | Documentation & closeout |

### Operators
| ID | Experience |
|---|---|
| OP_001, OP_002 | Expert |
| OP_003, OP_004 | Senior |
| OP_005, OP_006 | Mid-level |
| OP_007, OP_008 | Novice |

---

## Regenerating Data & Charts

Requires Python 3.8+ with: `pandas numpy matplotlib seaborn scipy`

```bash
# From project root:
python generate_data.py    # writes to data/
python generate_charts.py  # writes to charts/
```

---

## Website

`website/index.html` is a fully self-contained static page. It references chart
images via relative paths (`../charts/...`). Serve from project root or deploy
as a static site.

```bash
# Quick local server from project root:
python -m http.server 8080
# Then open: http://localhost:8080/website/
```

### Tabs
1. Overview — card gallery linking to each visualization type
2. Dotted Chart — temporal scatter of all interactions
3. Directly-Follows Graph — phase-level process model
4. Sankey Flow — proportional volume flow through phases
5. Heatmap — UI element × phase interaction density
6. Variant Comparison — phase duration by experience level
7. Phase Timeline — Gantt view of all procedures
8. Dwell Time — ridge density plot of interaction engagement
9. Transition Matrix — Markov-style phase transition probabilities

---

## Extension Ideas for Claude Code

- Replace static PNGs with interactive Plotly/D3 charts embedded in the page
- Add a data table viewer tab showing raw event_log.csv filterable by operator/phase
- Add operator filter controls to dynamically subset displayed charts
- Implement Plotly Sankey for a true interactive flow diagram
- Add a procedure player — step through a single case's events over time
- Export filtered subsets to XES format for compatibility with ProM / pm4py
- Build an HMM phase classifier using transition_matrix.csv as the prior
