# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Adapter classification on top of MedImageInsight embeddings.

Loads a pickled sklearn classifier trained in
``chapters/chapter2-foundation-models/extra-credit/notebooks/02-train-adapter.ipynb`` and applies it to a
fresh image embedding from MI2.

The adapter bundle (``adapter_<head>.joblib``) carries:

- ``model``         — fitted sklearn estimator with ``predict_proba``
- ``labels``        — class names in column order of ``predict_proba``
- ``preprocess``    — dict of preprocess kwargs used when training embeddings;
                      we forward these to ``mi2_client.get_embedding`` so the
                      inference recipe matches training exactly.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from workshop import mi2_client

# Resolves to <workspace-root>/models/ (parents[2] climbs out of mcp/medimageinsight-server/).
_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

_VALID_HEADS = ("svm", "mlp")


def _load_bundle(head: str) -> dict:
    if head not in _VALID_HEADS:
        raise ValueError(f"head must be one of {_VALID_HEADS} (got {head!r})")
    return joblib.load(_MODELS_DIR / f"adapter_{head}" / "weights.joblib")


def classify(
    file_path: str,
    head: str = "mlp",
) -> dict[str, str]:
    """Classify a chest X-ray with a trained adapter on top of MedImageInsight.

    Loads the requested adapter (``adapter_<head>.joblib``), embeds the image
    with MI2 using the same preprocessing recipe the adapter was trained on,
    and returns a per-label call:

    - ``"positive"`` — score ≥ Youden-J threshold (rule-in).
    - ``"negative"`` — score ≤ sens90 threshold (rule-out, ≥0.90 sensitivity).
    - ``"possible"`` — score between the two (cannot rule in or out).

    Both thresholds are fit per label during training and stored in the
    adapter bundle.

    Args:
        file_path: Path to the image file (PNG or JPEG).
        head: Which trained head to use — ``"mlp"`` (default) or ``"svm"``.

    Returns:
        Dictionary mapping each label to ``"positive"``, ``"possible"``,
        or ``"negative"``.
    """
    bundle = _load_bundle(head)
    labels = list(bundle["labels"])
    op_points = bundle.get("operating_points") or {}

    with open(file_path, "rb") as f:
        image_bytes = f.read()
    feats = np.asarray(
        mi2_client.get_embedding(image_bytes), dtype=np.float32
    ).reshape(1, -1)

    proba = bundle["model"].predict_proba(feats)[0]
    out: dict[str, str] = {}
    for lbl, p in zip(labels, proba):
        op = op_points.get(lbl, {})
        rule_in = float(op.get("youden_j", 0.5))
        rule_out = float(op.get("sens90", 0.0))
        score = float(p)
        if score >= rule_in:
            out[lbl] = "positive"
        elif score <= rule_out:
            out[lbl] = "negative"
        else:
            out[lbl] = "possible"
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MI2 trained adapter classification (standalone, bypasses MCP)."
    )
    parser.add_argument(
        "image",
        help="path to a chest X-ray image (e.g., samples/00026132_011.png)",
    )
    parser.add_argument(
        "--head",
        default="mlp",
        choices=["mlp", "svm"],
        help="adapter head to use (default: mlp)",
    )
    args = parser.parse_args()

    result = classify(args.image, head=args.head)
    for label, bucket in result.items():
        print(f"{label:30s} {bucket}")
