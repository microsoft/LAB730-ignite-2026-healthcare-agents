"""Aggregate per-case eval scores by confidence bucket.

Joins per-case metric scores with per-case confidence (from output.jsonl) and
produces a wide-format CSV: one row per confidence bucket, one column per
metric found in the scores file. Always emits an `all` row first. Prints
Markdown tables to stdout.

Usage:
    # Single result-dir:
    uv run python .github/skills/summarize-eval/eval_summary.py --result-dir <dir>

    # Compare two dirs:
    uv run python .github/skills/summarize-eval/eval_summary.py \\
        --baseline <baseline-dir> --candidate <candidate-dir>

Reads:
    <result-dir>/output.jsonl                                  (id, confidence)
    <result-dir>/section_<section>_scores.csv                  (study_id, metric cols)
    <result-dir>/aggregated_classification_by_confidence.csv   (optional)

Writes:
    <result-dir>/aggregated_by_confidence_<section>.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ID_COL = "study_id"

# Friendlier headers for known per-case metrics. Any other numeric column in the
# scores file is shown under its own name.
# TODO(eval): align with the final brain MRI metric suite (Ignite 2026).
METRIC_DISPLAY = {
    "bleu_score": "BLEU",
    "bertscore": "BERTScore",
    "laterality_correct": "laterality",
    "diameter_abs_error_mm": "diameter-err-mm",
}
# Per-case metrics where lower is better; shown with a trailing arrow.
LOWER_IS_BETTER = {"diameter_abs_error_mm"}

CLS_RENAME = {
    "accuracy": "accuracy",
    "macro_f1": "macro-F1",
    "micro_f1": "micro-F1",
    "macro_sensitivity": "sensitivity",
    "macro_specificity": "specificity",
    "macro_balanced_acc": "bal-acc",
}
CLS_DISPLAY_ORDER = ["accuracy", "macro-F1", "micro-F1", "sensitivity", "specificity", "bal-acc"]

DELTA_CLS_METRICS = ["macro-F1", "sensitivity", "specificity", "accuracy"]


def _display_name(metric: str) -> str:
    name = METRIC_DISPLAY.get(metric, metric)
    return f"{name} \u2193" if metric in LOWER_IS_BETTER else name


def _to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            cells.append(f"{v:.3f}" if isinstance(v, float) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _aggregate_scores(result_dir: Path, section: str) -> pd.DataFrame:
    scores_path = result_dir / f"section_{section}_scores.csv"
    output_path = result_dir / "output.jsonl"
    if not scores_path.exists():
        raise SystemExit(f"missing scores file: {scores_path}")
    if not output_path.exists():
        raise SystemExit(f"missing output.jsonl: {output_path}")

    scores = pd.read_csv(scores_path, dtype={ID_COL: str})
    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    confs = pd.DataFrame(
        [
            {
                ID_COL: str(rec["id"]),
                "confidence": (rec.get("confidence") or "none").lower(),
            }
            for rec in records
        ]
    )
    metrics = [
        c
        for c in scores.select_dtypes(include=["number", "bool"]).columns
        if c not in (ID_COL, "confidence")
    ]
    df = scores.drop(columns=["confidence"], errors="ignore").merge(confs, on=ID_COL, how="left")
    df["confidence"] = df["confidence"].fillna("none")

    rows = [{"confidence": "all", "n": len(df), **{c: df[c].mean() for c in metrics}}]
    for bucket in ["high", "medium", "low", "none"]:
        sub = df[df["confidence"] == bucket]
        if len(sub) == 0:
            continue
        rows.append({"confidence": bucket, "n": len(sub), **{c: sub[c].mean() for c in metrics}})

    out = pd.DataFrame(rows)
    out.to_csv(result_dir / f"aggregated_by_confidence_{section}.csv", index=False)

    return out.rename(columns={c: _display_name(c) for c in metrics})[
        ["confidence", "n"] + [_display_name(c) for c in metrics]
    ]


def _load_cls(result_dir: Path) -> pd.DataFrame | None:
    path = result_dir / "aggregated_classification_by_confidence.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path).rename(columns=CLS_RENAME)
    keep = ["confidence", "n"] + [c for c in CLS_DISPLAY_ORDER if c in df.columns]
    return df[keep]


def _fmt_delta(v: float) -> str:
    if v >= 0:
        return f"+{v:.3f}"
    return f"-{abs(v):.3f}"


def _delta_table(
    base_scores: pd.DataFrame,
    cand_scores: pd.DataFrame,
    base_cls: pd.DataFrame | None,
    cand_cls: pd.DataFrame | None,
) -> str:
    def all_row(df: pd.DataFrame) -> pd.Series:
        return df[df["confidence"] == "all"].iloc[0]

    rows = []
    if base_cls is not None and cand_cls is not None:
        b, c = all_row(base_cls), all_row(cand_cls)
        for m in DELTA_CLS_METRICS:
            if m in b.index and m in c.index:
                rows.append({
                    "metric": m,
                    "baseline": f"{b[m]:.3f}",
                    "candidate": f"{c[m]:.3f}",
                    "\u0394": _fmt_delta(c[m] - b[m]),
                })

    b, c = all_row(base_scores), all_row(cand_scores)
    for m in base_scores.columns:
        if m in ("confidence", "n") or m not in c.index:
            continue
        rows.append({
            "metric": m,
            "baseline": f"{b[m]:.3f}",
            "candidate": f"{c[m]:.3f}",
            "\u0394": _fmt_delta(c[m] - b[m]),
        })

    cols = ["metric", "baseline", "candidate", "\u0394"]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, sep] + [
        "| " + " | ".join(row[col] for col in cols) + " |"
        for row in rows
    ]
    return "\n".join(lines)


def _print_dir(result_dir: Path, section: str) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    scores = _aggregate_scores(result_dir, section)
    print(_to_markdown(scores))
    cls = _load_cls(result_dir)
    if cls is not None:
        print()
        print(_to_markdown(cls))
    return scores, cls


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize eval result dirs as Markdown tables.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--result-dir", type=Path, metavar="DIR")
    mode.add_argument("--baseline", type=Path, metavar="DIR")
    ap.add_argument("--candidate", type=Path, metavar="DIR")
    ap.add_argument("--section", default="none", help="Report section suffix (default: none)")
    args = ap.parse_args()

    if args.baseline is not None and args.candidate is None:
        ap.error("--candidate is required when --baseline is given")
    if args.candidate is not None and args.baseline is None:
        ap.error("--baseline is required when --candidate is given")

    if args.result_dir is not None:
        _print_dir(args.result_dir, args.section)
    else:
        print(f"### baseline: {args.baseline.name}")
        base_scores, base_cls = _print_dir(args.baseline, args.section)
        print()
        print(f"### candidate: {args.candidate.name}")
        cand_scores, cand_cls = _print_dir(args.candidate, args.section)
        print()
        print("### delta (candidate \u2212 baseline, all row)")
        print(_delta_table(base_scores, cand_scores, base_cls, cand_cls))


if __name__ == "__main__":
    main()