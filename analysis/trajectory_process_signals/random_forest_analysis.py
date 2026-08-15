"""Evaluate nonlinear stock-Pi trajectory signal with task-held-out random forests."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from .baseline_analysis import (
    CATEGORICAL_CONTROL_NAMES,
    LENGTH_FEATURE_NAMES,
    MUTATION_STYLE_PREDICTOR_NAMES,
    OPENING_PREDICTOR_NAMES,
    PREDICTOR_SPECIFICATIONS,
    PROCESS_FEATURE_NAMES,
    SEQUENCE_PREDICTOR_NAMES,
    TEST_FLOW_PREDICTOR_NAMES,
    _binary_metrics,
    _bootstrap_task_log_loss_delta,
    build_task_folds,
)
from .extractor import SEQUENCE_FEATURE_NAMES

ALL_MEASURED_PREDICTOR_NAMES = tuple(
    dict.fromkeys(LENGTH_FEATURE_NAMES + PROCESS_FEATURE_NAMES + SEQUENCE_FEATURE_NAMES)
)
RANDOM_FOREST_SPECIFICATIONS: dict[str, tuple[str, ...]] = {
    "length": PREDICTOR_SPECIFICATIONS["length"],
    "test_flow": PREDICTOR_SPECIFICATIONS["test_flow"],
    "all_process": PREDICTOR_SPECIFICATIONS["all_process"],
    "all_measured": ALL_MEASURED_PREDICTOR_NAMES,
}
RANDOM_FOREST_PERMUTATION_FAMILIES: dict[str, tuple[str, ...]] = {
    "length": LENGTH_FEATURE_NAMES,
    "aggregate_process": PROCESS_FEATURE_NAMES,
    "opening": OPENING_PREDICTOR_NAMES,
    "mutation_style": MUTATION_STYLE_PREDICTOR_NAMES,
    "test_flow": TEST_FLOW_PREDICTOR_NAMES,
    "additional_sequence": tuple(
        name for name in SEQUENCE_FEATURE_NAMES if name not in SEQUENCE_PREDICTOR_NAMES
    ),
}
DEFAULT_RANDOM_FOREST_SEEDS = (1401, 2903, 4409)


@dataclass(frozen=True)
class RandomForestParameters:
    """Bound random-forest complexity for the small stock-Pi trajectory cohort."""

    max_depth: int | None
    min_samples_leaf: int
    max_features: str | float


DEFAULT_RANDOM_FOREST_PARAMETER_GRID = (
    RandomForestParameters(max_depth=4, min_samples_leaf=10, max_features="sqrt"),
    RandomForestParameters(max_depth=8, min_samples_leaf=10, max_features="sqrt"),
    RandomForestParameters(max_depth=None, min_samples_leaf=20, max_features="sqrt"),
    RandomForestParameters(max_depth=8, min_samples_leaf=20, max_features=0.5),
)


def encode_random_forest_design(
    train_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
    *,
    numeric_names: Sequence[str],
    categorical_names: Sequence[str],
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """Encode raw numeric values and training-only one-hot categories for a forest."""
    if len(set(numeric_names)) != len(numeric_names):
        raise ValueError("random forest numeric feature names must be unique")
    train_parts = [
        np.array(
            [[float(row[name]) for name in numeric_names] for row in train_rows],
            dtype=float,
        )
    ]
    test_parts = [
        np.array(
            [[float(row[name]) for name in numeric_names] for row in test_rows],
            dtype=float,
        )
    ]
    feature_names = list(numeric_names)
    for name in categorical_names:
        categories = sorted({str(row[name]) for row in train_rows})
        train_parts.append(
            np.array(
                [
                    [float(str(row[name]) == category) for category in categories]
                    for row in train_rows
                ],
                dtype=float,
            )
        )
        test_parts.append(
            np.array(
                [
                    [float(str(row[name]) == category) for category in categories]
                    for row in test_rows
                ],
                dtype=float,
            )
        )
        feature_names.extend(f"{name}={category}" for category in categories)
    train_matrix = np.hstack(train_parts)
    test_matrix = np.hstack(test_parts)
    if not np.isfinite(train_matrix).all() or not np.isfinite(test_matrix).all():
        raise ValueError("random forest design contains non-finite values")
    return train_matrix, test_matrix, tuple(feature_names)


def select_random_forest_parameters(
    rows: Sequence[dict[str, Any]],
    numeric_names: Sequence[str],
    *,
    inner_fold_count: int,
    parameter_grid: Sequence[RandomForestParameters],
    tuning_trees: int,
    tuning_seed: int,
) -> tuple[RandomForestParameters, list[dict[str, Any]]]:
    """Select forest complexity by macro-task log loss inside training tasks only."""
    if not parameter_grid:
        raise ValueError("random forest parameter grid must not be empty")
    folds = build_task_folds(rows, inner_fold_count)
    outcomes = np.array([float(row["reward_binary"]) for row in rows])
    tasks = [str(row["task"]) for row in rows]
    candidate_reports: list[dict[str, Any]] = []
    for candidate_index, parameters in enumerate(parameter_grid):
        predictions = np.full(len(rows), np.nan)
        fold_reports: list[dict[str, Any]] = []
        for fold_index, fold in enumerate(folds):
            test_tasks = set(fold["test_tasks"])
            train_indices = [
                index
                for index, row in enumerate(rows)
                if str(row["task"]) not in test_tasks
            ]
            test_indices = [
                index
                for index, row in enumerate(rows)
                if str(row["task"]) in test_tasks
            ]
            train_rows = [rows[index] for index in train_indices]
            test_rows = [rows[index] for index in test_indices]
            train_matrix, test_matrix, _ = encode_random_forest_design(
                train_rows,
                test_rows,
                numeric_names=numeric_names,
                categorical_names=CATEGORICAL_CONTROL_NAMES,
            )
            model = _fit_random_forest(
                train_matrix,
                outcomes[train_indices],
                parameters,
                trees=tuning_trees,
                seed=tuning_seed + candidate_index * 1009 + fold_index * 101,
                oob=False,
            )
            predictions[test_indices] = _success_probabilities(model, test_matrix)
            fold_reports.append(
                {
                    "fold": fold_index,
                    "train_tasks": fold["train_tasks"],
                    "test_tasks": fold["test_tasks"],
                }
            )
        metrics = _binary_metrics(outcomes, predictions, tasks)
        candidate_reports.append(
            {
                "parameters": asdict(parameters),
                "metrics": metrics,
                "inner_folds": fold_reports,
            }
        )
    selected_index = min(
        range(len(candidate_reports)),
        key=lambda index: (
            candidate_reports[index]["metrics"]["macro_task_log_loss"],
            index,
        ),
    )
    return parameter_grid[selected_index], candidate_reports


def evaluate_random_forest_held_out_tasks(
    rows: Sequence[dict[str, Any]],
    *,
    outer_fold_count: int,
    inner_fold_count: int,
    specifications: Mapping[str, tuple[str, ...]] = RANDOM_FOREST_SPECIFICATIONS,
    parameter_grid: Sequence[
        RandomForestParameters
    ] = DEFAULT_RANDOM_FOREST_PARAMETER_GRID,
    tuning_trees: int = 150,
    final_trees: int = 400,
    final_seeds: Sequence[int] = DEFAULT_RANDOM_FOREST_SEEDS,
    permutation_repeats: int = 8,
) -> dict[str, Any]:
    """Compare random-forest process specifications on wholly unseen tasks."""
    if "length" not in specifications:
        raise ValueError("random forest specifications must include length")
    if not final_seeds:
        raise ValueError("random forest final seeds must not be empty")
    if permutation_repeats < 1:
        raise ValueError("random forest permutation repeats must be positive")
    folds = build_task_folds(rows, outer_fold_count)
    outcomes = np.array([float(row["reward_binary"]) for row in rows])
    tasks = [str(row["task"]) for row in rows]
    predictions = {
        name: np.full(len(rows), np.nan, dtype=float) for name in specifications
    }
    permutation_reference = (
        "all_measured"
        if "all_measured" in specifications
        else "all_process"
        if "all_process" in specifications
        else None
    )
    permutation_predictions = {
        name: np.full(len(rows), np.nan, dtype=float)
        for name in RANDOM_FOREST_PERMUTATION_FAMILIES
    }
    fold_reports: list[dict[str, Any]] = []

    for fold_index, fold in enumerate(folds):
        test_tasks = set(fold["test_tasks"])
        train_indices = [
            index
            for index, row in enumerate(rows)
            if str(row["task"]) not in test_tasks
        ]
        test_indices = [
            index for index, row in enumerate(rows) if str(row["task"]) in test_tasks
        ]
        train_rows = [rows[index] for index in train_indices]
        test_rows = [rows[index] for index in test_indices]
        y_train = outcomes[train_indices]
        if len(set(y_train)) < 2:
            raise RuntimeError(
                f"outer fold {fold_index} training outcomes have one class"
            )
        fold_report: dict[str, Any] = {
            "fold": fold_index,
            "train_tasks": fold["train_tasks"],
            "test_tasks": fold["test_tasks"],
            "train_reps": len(train_indices),
            "test_reps": len(test_indices),
            "selected_parameters": {},
            "tuning": {},
            "oob_diagnostics": {},
        }
        for specification_index, (name, numeric_names) in enumerate(
            specifications.items()
        ):
            selected, tuning_reports = select_random_forest_parameters(
                train_rows,
                numeric_names,
                inner_fold_count=inner_fold_count,
                parameter_grid=parameter_grid,
                tuning_trees=tuning_trees,
                tuning_seed=100_000 + fold_index * 10_000 + specification_index * 1000,
            )
            train_matrix, test_matrix, feature_names = encode_random_forest_design(
                train_rows,
                test_rows,
                numeric_names=numeric_names,
                categorical_names=CATEGORICAL_CONTROL_NAMES,
            )
            models = []
            test_seed_predictions = []
            oob_seed_predictions = []
            for seed in final_seeds:
                model = _fit_random_forest(
                    train_matrix,
                    y_train,
                    selected,
                    trees=final_trees,
                    seed=int(seed),
                    oob=True,
                )
                models.append(model)
                test_seed_predictions.append(_success_probabilities(model, test_matrix))
                oob_seed_predictions.append(_success_oob_probabilities(model))
            predictions[name][test_indices] = np.mean(test_seed_predictions, axis=0)
            oob_predictions = np.mean(oob_seed_predictions, axis=0)
            fold_report["selected_parameters"][name] = asdict(selected)
            fold_report["tuning"][name] = tuning_reports
            fold_report["oob_diagnostics"][name] = _binary_metrics(
                y_train,
                oob_predictions,
                [str(row["task"]) for row in train_rows],
            )
            if name == permutation_reference:
                for family_index, (family, family_names) in enumerate(
                    RANDOM_FOREST_PERMUTATION_FAMILIES.items()
                ):
                    columns = _feature_family_columns(feature_names, family_names)
                    repeat_predictions = []
                    for repeat in range(permutation_repeats):
                        permuted_matrix = _permute_feature_family_within_tasks(
                            test_matrix,
                            test_rows,
                            columns,
                            seed=(
                                900_000
                                + fold_index * 10_000
                                + family_index * 100
                                + repeat
                            ),
                        )
                        repeat_predictions.extend(
                            _success_probabilities(model, permuted_matrix)
                            for model in models
                        )
                    permutation_predictions[family][test_indices] = np.mean(
                        repeat_predictions, axis=0
                    )
        fold_reports.append(fold_report)

    binary_metrics = {
        name: _binary_metrics(outcomes, values, tasks)
        for name, values in predictions.items()
    }
    specification_deltas = {
        name: _prediction_delta(
            outcomes,
            predictions["length"],
            values,
            tasks,
        )
        for name, values in predictions.items()
        if name != "length"
    }
    permutation_importance: dict[str, Any] = {}
    if permutation_reference is not None:
        for family, values in permutation_predictions.items():
            permuted_metrics = _binary_metrics(outcomes, values, tasks)
            permutation_importance[family] = {
                "permuted_metrics": permuted_metrics,
                "permuted_minus_unpermuted": _prediction_delta(
                    outcomes,
                    predictions[permutation_reference],
                    values,
                    tasks,
                ),
                "method": "jointly permute the family within each held-out task",
            }
    return {
        "design": {
            "outcome": "reward_binary (1=success, 0=failure)",
            "outer_evaluation": "deterministic folds holding out whole tasks",
            "inner_selection": (
                "deterministic task-disjoint folds minimizing macro-task log loss "
                "inside each outer training partition"
            ),
            "oob_role": (
                "training-only diagnostic; never used as final evidence or for "
                "parameter selection because OOB separates attempts rather than tasks"
            ),
            "categorical_controls": list(CATEGORICAL_CONTROL_NAMES),
            "specifications": {
                name: list(feature_names)
                for name, feature_names in specifications.items()
            },
            "permutation_reference": permutation_reference,
            "parameter_grid": [asdict(parameters) for parameters in parameter_grid],
            "tuning_trees": tuning_trees,
            "final_trees_per_seed": final_trees,
            "final_seeds": list(final_seeds),
            "permutation_repeats": permutation_repeats,
            "criterion": "log_loss",
            "class_weight": None,
            "outer_fold_count": outer_fold_count,
            "inner_fold_count": inner_fold_count,
        },
        "folds": fold_reports,
        "binary_metrics": binary_metrics,
        "specification_minus_length": specification_deltas,
        "oob_diagnostics": _summarize_oob_diagnostics(fold_reports, specifications),
        "permutation_family_importance": permutation_importance,
    }


def select_certain_source_mutation_rows(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep attempts with an observed source mutation and no prior shell uncertainty."""
    return [
        row
        for row in rows
        if float(row["has_successful_source_mutation"]) == 1.0
        and float(row["first_source_mutation_boundary_uncertain"]) == 0.0
    ]


def load_random_forest_feature_rows(path: Path) -> list[dict[str, Any]]:
    """Load only the pre-verifier columns required by the forest experiment."""
    numeric_names = set().union(*RANDOM_FOREST_SPECIFICATIONS.values())
    rows: list[dict[str, Any]] = []
    with path.open(newline="") as handle:
        for source in csv.DictReader(handle):
            row: dict[str, Any] = {
                "cell_id": source["cell_id"],
                "task": source["task"],
                "model": source["model"],
                "thinking_level": source["thinking_level"],
                "config": source["config"],
                "reward_binary": int(source["reward_binary"]),
            }
            row.update({name: float(source[name]) for name in numeric_names})
            rows.append(row)
    if not rows:
        raise ValueError(f"random forest feature input is empty: {path}")
    return rows


def _fit_random_forest(
    matrix: np.ndarray,
    outcomes: np.ndarray,
    parameters: RandomForestParameters,
    *,
    trees: int,
    seed: int,
    oob: bool,
) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=trees,
        criterion="log_loss",
        max_depth=parameters.max_depth,
        min_samples_leaf=parameters.min_samples_leaf,
        max_features=parameters.max_features,
        bootstrap=True,
        oob_score=oob,
        class_weight=None,
        n_jobs=-1,
        random_state=seed,
    )
    model.fit(matrix, outcomes.astype(int))
    return model


def _success_class_index(model: RandomForestClassifier) -> int:
    if not np.array_equal(np.asarray(model.classes_), np.array([0, 1])):
        raise RuntimeError(f"random forest has unexpected classes: {model.classes_}")
    return 1


def _success_probabilities(
    model: RandomForestClassifier, matrix: np.ndarray
) -> np.ndarray:
    return np.asarray(
        model.predict_proba(matrix)[:, _success_class_index(model)], dtype=float
    )


def _success_oob_probabilities(model: RandomForestClassifier) -> np.ndarray:
    probabilities = np.asarray(
        model.oob_decision_function_[:, _success_class_index(model)], dtype=float
    )
    if not np.isfinite(probabilities).all():
        raise RuntimeError("random forest OOB predictions contain non-finite values")
    return probabilities


def _feature_family_columns(
    encoded_names: Sequence[str], family_names: Sequence[str]
) -> list[int]:
    family = set(family_names)
    return [index for index, name in enumerate(encoded_names) if name in family]


def _permute_feature_family_within_tasks(
    matrix: np.ndarray,
    rows: Sequence[dict[str, Any]],
    columns: Sequence[int],
    *,
    seed: int,
) -> np.ndarray:
    permuted = matrix.copy()
    if not columns:
        return permuted
    rng = np.random.default_rng(seed)
    by_task: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_task[str(row["task"])].append(index)
    for indices in by_task.values():
        source_indices = rng.permutation(indices)
        permuted[np.ix_(indices, columns)] = matrix[np.ix_(source_indices, columns)]
    return permuted


def _prediction_delta(
    outcomes: np.ndarray,
    reference: np.ndarray,
    candidate: np.ndarray,
    tasks: Sequence[str],
) -> dict[str, Any]:
    reference_metrics = _binary_metrics(outcomes, reference, tasks)
    candidate_metrics = _binary_metrics(outcomes, candidate, tasks)
    return {
        "log_loss": candidate_metrics["log_loss"] - reference_metrics["log_loss"],
        "macro_task_log_loss": candidate_metrics["macro_task_log_loss"]
        - reference_metrics["macro_task_log_loss"],
        "brier": candidate_metrics["brier"] - reference_metrics["brier"],
        "auroc": candidate_metrics["auroc"] - reference_metrics["auroc"],
        "average_precision": candidate_metrics["average_precision"]
        - reference_metrics["average_precision"],
        "task_bootstrap_log_loss_delta_95pct": _bootstrap_task_log_loss_delta(
            outcomes,
            reference,
            candidate,
            tasks,
        ),
    }


def _summarize_oob_diagnostics(
    fold_reports: Sequence[dict[str, Any]],
    specifications: Mapping[str, tuple[str, ...]],
) -> dict[str, Any]:
    metric_names = (
        "log_loss",
        "macro_task_log_loss",
        "brier",
        "auroc",
        "average_precision",
    )
    return {
        "caveat": (
            "OOB predictions separate bootstrapped attempts, not whole tasks; use only "
            "as a training diagnostic and compare against outer task-held-out metrics"
        ),
        "mean_across_outer_training_partitions": {
            name: {
                metric: float(
                    np.mean(
                        [fold["oob_diagnostics"][name][metric] for fold in fold_reports]
                    )
                )
                for metric in metric_names
            }
            for name in specifications
        },
    }


def _linear_comparison(
    forest_evaluation: dict[str, Any], linear_evaluation: dict[str, Any]
) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    for name, forest_metrics in forest_evaluation["binary_metrics"].items():
        linear_metrics = linear_evaluation["binary_metrics"][name]
        comparison[name] = {
            metric: float(forest_metrics[metric] - linear_metrics[metric])
            for metric in (
                "log_loss",
                "macro_task_log_loss",
                "brier",
                "auroc",
                "average_precision",
            )
        }
    return comparison


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_metadata(repo_root: Path) -> dict[str, str]:
    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

    return {
        "worktree": str(repo_root),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "base_ref": "origin/master",
        "base_revision": git("rev-parse", "origin/master"),
    }


def run_random_forest_analysis(
    feature_path: Path,
    linear_evaluation_path: Path,
    output_path: Path,
    *,
    outer_fold_count: int,
    inner_fold_count: int,
    tuning_trees: int,
    final_trees: int,
    permutation_repeats: int,
) -> dict[str, Any]:
    """Run the nonlinear comparison from the committed stock-Pi feature table."""
    rows = load_random_forest_feature_rows(feature_path)
    evaluation = evaluate_random_forest_held_out_tasks(
        rows,
        outer_fold_count=outer_fold_count,
        inner_fold_count=inner_fold_count,
        tuning_trees=tuning_trees,
        final_trees=final_trees,
        permutation_repeats=permutation_repeats,
    )
    linear_evaluation = json.loads(linear_evaluation_path.read_text())
    evaluation["forest_minus_linear"] = _linear_comparison(
        evaluation, linear_evaluation
    )
    certain_boundary_rows = select_certain_source_mutation_rows(rows)
    certain_boundary_evaluation = evaluate_random_forest_held_out_tasks(
        certain_boundary_rows,
        outer_fold_count=outer_fold_count,
        inner_fold_count=inner_fold_count,
        tuning_trees=tuning_trees,
        final_trees=final_trees,
        permutation_repeats=permutation_repeats,
    )
    certain_boundary_linear = linear_evaluation["cohort_sensitivities"][
        "certain_first_source_mutation"
    ]["evaluation"]
    certain_boundary_evaluation["forest_minus_linear"] = _linear_comparison(
        certain_boundary_evaluation, certain_boundary_linear
    )
    evaluation["cohort_sensitivities"] = {
        "certain_first_source_mutation": {
            "reps": len(certain_boundary_rows),
            "excluded_reps": len(rows) - len(certain_boundary_rows),
            "evaluation": certain_boundary_evaluation,
        }
    }
    evaluation["provenance"] = {
        "analysis": "stock-pi-random-forest-trajectory-signals",
        "git": _git_metadata(Path(__file__).resolve().parents[2]),
        "feature_path": str(feature_path.resolve()),
        "feature_sha256": _sha256(feature_path),
        "feature_rows": len(rows),
        "tasks": len({str(row["task"]) for row in rows}),
        "linear_evaluation_path": str(linear_evaluation_path.resolve()),
        "linear_evaluation_sha256": _sha256(linear_evaluation_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n")
    return evaluation


def main() -> None:
    """Run the stock-Pi random-forest trajectory experiment."""
    parser = argparse.ArgumentParser(
        description="Evaluate stock-Pi trajectory features with task-held-out forests."
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path(
            "analysis/trajectory_process_signals/artifacts/baseline_features.csv"
        ),
    )
    parser.add_argument(
        "--linear-evaluation",
        type=Path,
        default=Path(
            "analysis/trajectory_process_signals/artifacts/held_out_task_evaluation.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "analysis/trajectory_process_signals/artifacts/random_forest_evaluation.json"
        ),
    )
    parser.add_argument("--outer-folds", type=int, default=4)
    parser.add_argument("--inner-folds", type=int, default=3)
    parser.add_argument("--tuning-trees", type=int, default=150)
    parser.add_argument("--final-trees", type=int, default=400)
    parser.add_argument("--permutation-repeats", type=int, default=8)
    arguments = parser.parse_args()
    evaluation = run_random_forest_analysis(
        arguments.features,
        arguments.linear_evaluation,
        arguments.output,
        outer_fold_count=arguments.outer_folds,
        inner_fold_count=arguments.inner_folds,
        tuning_trees=arguments.tuning_trees,
        final_trees=arguments.final_trees,
        permutation_repeats=arguments.permutation_repeats,
    )
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "rows": evaluation["provenance"]["feature_rows"],
                "tasks": evaluation["provenance"]["tasks"],
                "binary_metrics": evaluation["binary_metrics"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
