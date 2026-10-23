# EC499 Report Artifacts

This folder is a self-contained report package for **Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network**. It is named `report_artifacts` so reproduction commands remain meaningful outside this development environment.

- `main.tex` — complete LaTeX report with an embedded bibliography
- `main.pdf` — compiled report
- `figures/` — 14 figures referenced by `main.tex`
- `data/` — five machine-readable result files regenerated from the current code and model

Build from this directory with:

```bash
tectonic main.tex
```

The report distinguishes fresh simulation results, analytical queueing plots, archived training telemetry, dashboard screenshots, and unverified live-controller capabilities. Its robustness study repeats the five-topology tournament for workload seeds 42--46 in both pure and safety-policy modes and applies a two-way cluster bootstrap. Regenerate the experiment artifacts using the commands in Chapter 11 before changing reported numerical values.
