# Report delivery

How results analyses are delivered in this repo. A results analysis — a
per-config comparison, run summary, or post-run analysis — is a
**self-contained HTML page served on the tailnet**, never plain prose. This is
the user's preferred review format; use it by default.

## Report home

- Standalone deliverables (comparisons, run summaries, leaderboards) live at
  `reports/<slug>/index.html`.
- Reports that ship inside a broader analysis — alongside scripts, JSON
  artifacts, and probe outputs — live at `analysis/<topic>/index.html`.

Both are first-class. Pick based on whether the report is the whole deliverable
(`reports/`) or one output of an analysis workflow (`analysis/`).

## Design system

Match the project report design system — one visual language across all
reports.

- CSS variables: `--bg`, `--surface`, `--ink`, `--blue`, `--green`, `--red`,
  `--amber`.
- Structural classes: `.hero`, `.stats`/`.stat`, `.pill good/bad/caution/neutral`,
  comparison `<table>` with verdict `.tag`s, `.callout`.
- Charts are deterministic CSS/SVG — never AI-generated charts or image-model
  output for data.
- Always include: hero + verdict pills + KPI stat cards, the key comparison
  table(s), and a conclusion in callouts.

Reference templates (copy structure, not content):

- `reports/om-memory-pilot-w10/index.html`
- `analysis/omp-vs-pi-36v2/index.html`

## Serving

Serve from the report directory inside a tmux session:

```sh
python3 -m http.server <port> --bind 0.0.0.0
```

- Pick a free port; 8788, 8789, and 5173 are taken.
- Verify `curl http://100.112.72.93:<port>/` returns 200 before handing off the
  URL.
- lavish-axi has no tailnet host-bind, so do not use it for tailnet serving.

## Completion criterion

The report file exists at its canonical home, the tailnet URL returns 200, and
the page renders hero, verdict pills, KPI cards, comparison table(s), and a
callout conclusion from the design system.
