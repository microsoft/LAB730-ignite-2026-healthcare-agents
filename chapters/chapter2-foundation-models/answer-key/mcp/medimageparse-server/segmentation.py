# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Catalog-driven 3D segmentation with source-grid NIfTI masks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from workshop.mip_client import MIPClient

MASKS_DIR = Path(__file__).resolve().parents[2] / "outputs" / "masks"
CATALOG = json.loads(
    Path(__file__).with_name("models.json").read_text(encoding="utf-8")
)


def list_models() -> list[dict]:
    """List available 3D MRI models, descriptions, and ordered prompt views.

    Choose a model suited to the image and request only one view per segment
    call: views can overlap, but each output voxel holds one label. Pass the
    full prompts verbatim in their listed order. Subsets are allowed; output
    label i always corresponds to prompts[i-1] in that call, with 0 background.
    """
    return [
        {key: entry[key] for key in ("model", "description", "views")}
        for entry in CATALOG
    ]


def segment(image_path: str, model: str, prompts: list[str]) -> dict:
    """Segment a 3D NIfTI image using a model and prompts from list_models.

    image_path is an absolute image path. Send verbatim prompts from one view
    per call. The client handles preprocessing and restores the source grid.
    Returns mask_path and labels with label, prompt, detected, and volume_ml
    (one decimal). Label i matches prompts[i-1]; 0 is background. Pass mask_path
    and a label to measure for component volumes, extents, and centroids.
    """
    entry = next((entry for entry in CATALOG if entry["model"] == model), None)
    if entry is None:
        raise ValueError(
            f"Unknown model {model!r}; valid names: {[entry['model'] for entry in CATALOG]}"
        )
    mask = MIPClient.from_env(
        entry["deployment"], **entry.get("preprocessing", {})
    ).segment(image_path, prompts)
    image_stem = Path(image_path).name.removesuffix(".gz").removesuffix(".nii")
    prompt_hash = hashlib.sha256(json.dumps(prompts).encode("utf-8")).hexdigest()[:8]
    stem = f"{image_stem}__{model}__{prompt_hash}"
    MASKS_DIR.mkdir(parents=True, exist_ok=True)
    mask_path = MASKS_DIR / f"{stem}.nii.gz"
    nib.save(mask, mask_path)
    (MASKS_DIR / f"{stem}.json").write_text(
        json.dumps(
            {
                "image_path": image_path,
                "model": model,
                "deployment": entry["deployment"],
                "prompts": prompts,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    labels = np.asanyarray(mask.dataobj)
    voxel_ml = abs(float(np.linalg.det(mask.affine[:3, :3]))) / 1000
    return {
        "mask_path": str(mask_path),
        "labels": [
            {
                "label": label,
                "prompt": prompt,
                "detected": bool(np.any(labels == label)),
                "volume_ml": round(
                    float(np.count_nonzero(labels == label)) * voxel_ml, 1
                ),
            }
            for label, prompt in enumerate(prompts, start=1)
        ],
    }
