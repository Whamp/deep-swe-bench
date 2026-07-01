"""Offline GEPA prompt-optimization sidecar for pi-observational-memory.

The package code lives in importable ``analysis.om_gepa`` while durable artifacts and
human-facing wrappers live in ``analysis/om-gepa``.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "analysis" / "om-gepa"
DEFAULT_CONFIG = REPO_ROOT / "configs" / "observational-memory"
DEFAULT_EXTENSION_SRC = DEFAULT_CONFIG / "extensions" / "pi-observational-memory" / "src"
