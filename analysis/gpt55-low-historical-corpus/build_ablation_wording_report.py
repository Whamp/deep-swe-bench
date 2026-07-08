#!/usr/bin/env python3
from __future__ import annotations

import difflib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "analysis/gpt55-low-historical-corpus"
REPORT_DIR = ROOT / "reports/gpt55-low-next-ablation-wording"
OUT_JSON = ANALYSIS_DIR / "next_ablation_wording_changes.json"
OUT_HTML = REPORT_DIR / "index.html"

BASELINE = "baseline-wf-only"
VARIANTS = [
    {
        "config": "baseline-wf-no-repro-script",
        "label": "Workflow checklist without explicit repro-script step",
        "intent": "Test whether the winning workflow prompt depends on requiring a dedicated reproduction script.",
    },
    {
        "config": "baseline-wf-no-commit",
        "label": "Workflow checklist without commit step",
        "intent": "Test whether the commit instruction is useful completion/capture guidance or unnecessary benchmark overhead.",
    },
    {
        "config": "baseline-wf-tight-checklist",
        "label": "Tight workflow checklist",
        "intent": "Test whether compact ordered structure is enough, or whether the longer original wording matters.",
    },
]


def read(path: Path) -> str:
    return path.read_text()


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


def file_info(config: str) -> dict[str, object]:
    root = ROOT / "configs" / config
    files = sorted(p.name for p in root.iterdir() if p.is_file())
    orchestration = read(root / "orchestration.md")
    smoke = json.loads(read(root / "smoke.json"))
    readme = read(root / "README.md")
    return {
        "config": config,
        "path": str(root.relative_to(ROOT)),
        "files": files,
        "orchestration": orchestration,
        "orchestration_chars": len(orchestration),
        "orchestration_bytes": len(orchestration.encode()),
        "readme": readme,
        "smoke": smoke,
        "smoke_config": smoke["equalsResultValues"].get("config"),
        "smoke_orchestration_chars": smoke["equalsResultValues"].get("orchestration_chars"),
        "smoke_system_preamble_chars": smoke["equalsResultValues"].get("system_preamble_chars"),
        "smoke_model": smoke["equalsResultValues"].get("model"),
        "smoke_thinking_level": smoke["equalsResultValues"].get("thinking_level"),
        "has_system_preamble": (root / "system_preamble.md").exists(),
        "has_extensions_dir": (root / "extensions").exists(),
        "has_model_leaf_files": any(p.is_dir() for p in root.iterdir()),
    }


def unified_diff(base_text: str, variant_text: str, base: str, variant: str) -> str:
    return "".join(difflib.unified_diff(
        base_text.splitlines(keepends=True),
        variant_text.splitlines(keepends=True),
        fromfile=f"configs/{base}/orchestration.md",
        tofile=f"configs/{variant}/orchestration.md",
        lineterm="",
    ))


def validate(data: dict[str, object]) -> None:
    baseline = data["baseline"]
    for variant in data["variants"]:
        info = variant["file_info"]
        if info["files"] != baseline["files"]:
            raise AssertionError(f"{info['config']} file list changed: {info['files']} vs {baseline['files']}")
        if info["smoke_config"] != info["config"]:
            raise AssertionError(f"smoke config mismatch for {info['config']}")
        if info["smoke_orchestration_chars"] != info["orchestration_chars"]:
            raise AssertionError(f"smoke chars mismatch for {info['config']}")
        if info["smoke_system_preamble_chars"] != 0:
            raise AssertionError(f"system preamble chars not zero for {info['config']}")
        if info["smoke_model"] != "openai-codex/gpt-5.5" or info["smoke_thinking_level"] != "low":
            raise AssertionError(f"model/thinking changed for {info['config']}")
        if info["has_system_preamble"] or info["has_extensions_dir"] or info["has_model_leaf_files"]:
            raise AssertionError(f"unexpected extra config surface for {info['config']}")


def build() -> dict[str, object]:
    baseline = file_info(BASELINE)
    variants = []
    for spec in VARIANTS:
        info = file_info(spec["config"])
        variants.append({
            **spec,
            "file_info": info,
            "orchestration_diff_vs_baseline": unified_diff(
                baseline["orchestration"],
                info["orchestration"],
                BASELINE,
                spec["config"],
            ),
            "metadata_changes_allowed": [
                "README title/path and orchestration character count",
                "smoke equalsResultValues.config",
                "smoke equalsResultValues.orchestration_chars",
                "smoke requireRepoFiles/requireRepoText/forbidRepoText paths",
                "smoke requireRepoText exact anchor text",
            ],
            "unchanged_surfaces": [
                "No system_preamble.md",
                "No extensions/ directory",
                "No skills or model leaf files",
                "Same smoke model openai-codex/gpt-5.5",
                "Same smoke thinking level low",
                "Same system_preamble_chars = 0",
            ],
        })
    data = {
        "title": "Next GPT-5.5 low workflow prompt ablation wording",
        "scope": "Create prompt-only configs for the approved workflow-checklist ablation sweep; do not launch benchmark runs.",
        "baseline": baseline,
        "variants": variants,
        "validation_rule": "Each variant directory must contain the same file set as baseline-wf-only: README.md, orchestration.md, smoke.json. The only prompt-surface change is orchestration.md; metadata changes are limited to config name, paths, and orchestration character count so smoke remains accurate.",
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "html": str(OUT_HTML.relative_to(ROOT)),
        },
    }
    validate(data)
    return data


def render_variant(variant: dict[str, object]) -> str:
    info = variant["file_info"]
    allowed = "".join(f"<li>{h(item)}</li>" for item in variant["metadata_changes_allowed"])
    unchanged = "".join(f"<li>{h(item)}</li>" for item in variant["unchanged_surfaces"])
    files = ", ".join(f"<code>{h(file)}</code>" for file in info["files"])
    return f'''<section class="card"><h2>{h(variant['config'])}</h2><p><b>{h(variant['label'])}</b> — {h(variant['intent'])}</p><div class="meta"><span class="pill neutral">{h(info['orchestration_chars'])} chars</span><span class="pill good">system preamble 0</span><span class="pill good">no extensions</span><span class="pill good">no model leaf files</span></div><p class="muted">Files: {files}</p><h3>Final exact orchestration.md</h3><pre>{h(info['orchestration'])}</pre><h3>Unified diff vs baseline-wf-only/orchestration.md</h3><pre class="diff">{h(variant['orchestration_diff_vs_baseline'])}</pre><details><summary>Allowed metadata changes, not prompt behavior changes</summary><ul>{allowed}</ul><h4>Verified unchanged surfaces</h4><ul>{unchanged}</ul></details></section>'''


def render(data: dict[str, object]) -> str:
    baseline = data["baseline"]
    variants_html = "\n".join(render_variant(variant) for variant in data["variants"])
    rows = "".join(
        f"<tr><td><code>{h(v['config'])}</code></td><td>{h(v['label'])}</td><td>{h(v['file_info']['orchestration_chars'])}</td><td>{h(v['intent'])}</td></tr>"
        for v in data["variants"]
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{h(data['title'])}</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,#183f55,#07111f 45%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1240px;margin:0 auto;padding:34px 22px 70px}}.hero,.card,.callout{{background:rgba(15,29,49,.93);border:1px solid var(--line);border-radius:24px;padding:24px;box-shadow:0 20px 80px rgba(0,0,0,.24)}}.hero{{padding:34px;background:linear-gradient(135deg,rgba(52,211,153,.18),rgba(15,29,49,.95) 48%,rgba(96,165,250,.12))}}h1{{font-size:clamp(34px,5vw,64px);line-height:.95;letter-spacing:-.055em;margin:10px 0 16px}}h2{{margin:0 0 12px;font-size:25px;letter-spacing:-.02em}}h3{{margin:18px 0 8px}}p,li{{color:#dbe7fb}}.kicker{{color:var(--green);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:900}}.pill{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:850;border:1px solid var(--line);background:#0b1728;color:var(--muted);margin:2px}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.grid{{display:grid;gap:18px}}.meta{{display:flex;gap:8px;flex-wrap:wrap}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.66);margin:18px 0 24px}}th,td{{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code,pre{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:8px}}code{{padding:1px 5px;font-size:12px}}pre{{white-space:pre-wrap;padding:14px;overflow:auto}}.diff{{color:#f8fafc}}.muted,.src{{color:var(--muted);font-size:12px}}details{{margin-top:12px}}summary{{cursor:pointer;color:#bfdbfe;font-weight:800}}@media(max-width:860px){{table{{display:block;overflow-x:auto}}}}
</style></head><body><main><section class="hero"><div class="kicker">Approved config wording · no benchmark run launched</div><h1>Three prompt-only ablation configs, with exact wording changes.</h1><p>{h(data['scope'])}</p><div class="meta"><span class="pill good">same file set as baseline-wf-only</span><span class="pill good">no system preamble</span><span class="pill good">no extensions/skills/model leaves</span><span class="pill caution">only orchestration wording differs</span></div><p class="src">Baseline source: <code>configs/{h(BASELINE)}/orchestration.md</code> ({h(baseline['orchestration_chars'])} chars).</p></section><section class="callout"><h2>Baseline wording</h2><pre>{h(baseline['orchestration'])}</pre></section><section class="card"><h2>Summary</h2><table><thead><tr><th>Config</th><th>Variant</th><th>Chars</th><th>Question answered</th></tr></thead><tbody>{rows}</tbody></table><p class="muted">Validation rule: {h(data['validation_rule'])}</p></section><div class="grid">{variants_html}</div><section class="callout"><h2>Generated artifacts</h2><ul><li><code>{h(data['outputs']['json'])}</code></li><li><code>{h(data['outputs']['html'])}</code></li></ul></section></main></body></html>'''


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = build()
    OUT_JSON.write_text(json.dumps(data, indent=2))
    OUT_HTML.write_text(render(data))
    print("wrote", OUT_JSON.relative_to(ROOT), OUT_JSON.stat().st_size)
    print("wrote", OUT_HTML.relative_to(ROOT), OUT_HTML.stat().st_size)


if __name__ == "__main__":
    main()
