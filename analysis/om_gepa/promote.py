from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path

from . import DEFAULT_CONFIG, REPO_ROOT
from .common import prompt_file_for_role, prompt_patch, ts_template_literal


def constant_for_role(role: str) -> str:
    return "OBSERVER_SYSTEM" if role == "observer" else "REFLECTOR_SYSTEM"


def prompt_ts_text(role: str, prompt: str) -> str:
    return f"export const {constant_for_role(role)} = {ts_template_literal(prompt)};\n"


def changed_files(a: Path, b: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(p for p in b.rglob("*") if p.is_file()):
        rel = path.relative_to(b)
        left = a / rel
        if not left.exists() or not filecmp.cmp(left, path, shallow=False):
            files.append(str(rel))
    return files


def promote(role: str, candidate_prompt: Path, base_config: Path, new_config: Path, dry_run: bool) -> dict[str, object]:
    prompt_text = candidate_prompt.read_text(encoding="utf-8")
    patch = prompt_patch(role, prompt_text, base_config)
    if dry_run:
        return {"role": role, "dry_run": True, "patch": patch}
    if new_config.exists():
        raise SystemExit(f"Refusing to overwrite existing config: {new_config}")
    shutil.copytree(base_config, new_config, symlinks=True)
    target = prompt_file_for_role(new_config, role)
    target.write_text(prompt_ts_text(role, prompt_text), encoding="utf-8")
    readme = new_config / "README.md"
    with readme.open("a", encoding="utf-8") as f:
        f.write(
            "\n\n## OM GEPA prompt promotion\n\n"
            f"This config was promoted by `analysis.om_gepa.promote` from `{base_config.relative_to(REPO_ROOT)}`.\n\n"
            f"Mutable role: `{role}` prompt only. Dropper is intentionally excluded. Runtime files, tool schemas, ledger logic, and consolidation logic should match the base config.\n"
        )
    changed = changed_files(base_config, new_config)
    allowed = {str(prompt_file_for_role(base_config, role).relative_to(base_config)), "README.md"}
    unexpected = [p for p in changed if p not in allowed]
    if unexpected:
        raise SystemExit(f"Unexpected changed files after promotion: {unexpected}")
    (new_config / "om-gepa-promotion.patch").write_text(patch, encoding="utf-8")
    return {"role": role, "dry_run": False, "new_config": str(new_config), "changed_files": changed}


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a held-out-validated observer/reflector prompt into a new config. Dropper is excluded.")
    parser.add_argument("--role", choices=["observer", "reflector"], required=True)
    parser.add_argument("--candidate-prompt", type=Path, required=True)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--new-config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = promote(args.role, args.candidate_prompt, args.base_config, args.new_config, args.dry_run)
    if args.dry_run:
        print(result["patch"])
    else:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
