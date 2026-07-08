"""Pure-address results-tree module.

Centralises the model-leaf derivation and the results-path grammar
(`results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/`) behind one small,
frozen interface (Tree -> Cell). Derives paths, checks existence, and iterates
cells only — it performs NO writes. Consumes ``lib.model_leaf`` (executor-only)
and ``lib.REPO``; does not re-expose leaf derivation or advisor logic (the
results tree is executor-only per ADR-0001).

This is the expand step of an expand-contract refactor: it lands beside the
existing duplicated construction without changing any caller.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from harness import lib


@dataclass(frozen=True)
class Cell:
    """The on-disk address of one rep: its directory plus canonical paths.

    A rep's container (CONTEXT.md ``cell``), distinct from the rep (the run).
    Identity (config, task, rep) is carried so readers iterating results know
    which rep each result belongs to. ``dir`` is the escape hatch for
    non-canonical files (tool-usage.jsonl, pi-agent/, ...).
    """

    config: str
    task: str
    rep: int
    dir: Path

    @property
    def result(self) -> Path:
        return self.dir / "result.json"

    @property
    def transient_error(self) -> Path:
        # Sentinel written on a rep-killing transient provider error (exit 75).
        return self.dir / "transient_error.json"

    @property
    def artifacts(self) -> Path:
        return self.dir / "artifacts"

    @property
    def verifier(self) -> Path:
        return self.dir / "verifier"

    @property
    def logs(self) -> Path:
        return self.dir / "logs"

    @property
    def session(self) -> Path:
        return self.dir / "session"

    def has_result(self) -> bool:
        # The resume existence check: a rep is done iff its result.json exists.
        return self.result.exists()


@dataclass(frozen=True)
class Tree:
    """The results tree for one (model, thinking): repo/results/<leaf>/<thinking>."""

    model: str
    thinking: str
    repo: Path

    @classmethod
    def of(cls, model: str, thinking: str, repo: Path | None = None) -> "Tree":
        """Sole factory. repo defaults to lib.REPO. The leaf is sealed — a
        derived property, not a stored field — so no construction path can
        inject an advisor (+advisor) leaf; the results tree is executor-only
        (ADR-0001)."""
        repo = lib.REPO if repo is None else repo
        return cls(model=model, thinking=thinking, repo=repo)

    @property
    def leaf(self) -> str:
        # Sealed: always the executor-only lib.model_leaf(model). Derived, not
        # stored, so it cannot be bypassed by direct construction.
        return lib.model_leaf(self.model)

    @property
    def root(self) -> Path:
        # repo/results/<leaf>/<thinking> — the escape hatch for tree-level
        # non-canonical files (a future comparison manifest, etc.).
        return self.repo / "results" / self.leaf / self.thinking

    @property
    def results_jsonl(self) -> Path:
        return self.root / "results.jsonl"

    def log_file(self, config: str, task: str, rep: int) -> Path:
        # Flat per-cell log under <thinking>/logs/ (run_batch log_path grammar).
        return self.root / "logs" / f"{task}__{config}__rep{rep}.log"

    def cell(self, config: str, task: str, rep: int) -> Cell:
        return Cell(
            config=config,
            task=task,
            rep=rep,
            dir=self.root / config / task / f"rep{rep}",
        )

    def has_results(self, config: str) -> bool:
        # config-level existence (resume gate): some result.json under
        # root/config/*/rep*/. Mirrors run_batch.config_has_results.
        base = self.root / config
        return base.exists() and any(base.glob("*/rep*/result.json"))

    def cells(self, configs: list[str] | None = None) -> Iterator[Cell]:
        # Yield a Cell for every existing result.json, sorted by
        # (config, task, rep-as-int) so rep10 follows rep2 — lexicographic glob
        # would order rep10 before rep2. `configs` restricts the config scope.
        found: list[Cell] = []
        for p in self.root.glob("*/*/rep*/result.json"):
            config, task, repdir = p.relative_to(self.root).parts[:3]
            if configs is not None and config not in configs:
                continue
            found.append(self.cell(config, task, int(repdir[3:])))
        found.sort(key=lambda c: (c.config, c.task, c.rep))
        yield from found
