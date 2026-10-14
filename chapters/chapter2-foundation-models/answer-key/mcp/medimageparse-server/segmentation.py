# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Catalog-driven 3D segmentation with source-grid NIfTI masks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np

import figures
from workshop.mip_client import MIPClient

AUDIT_DIR = Path(__file__).resolve().parents[2] / "audit-log"
REPO_ROOT = Path(__file__).resolve().parents[5]
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
    Returns audit_dir, mask_path, labels with label, prompt, detected, and
    volume_ml (one decimal), and images. Label i matches prompts[i-1]; 0 is
    background. audit_dir is audit-log/<image path>/, which holds the mask,
    prompt sidecar, and two review images: film-grid.png (image only) and
    <mask stem>.film-grid.png (mask overlay). Pass the tumor-components
    mask_path to clean_segmentation before describe_lesions.
    """
    entry = next((entry for entry in CATALOG if entry["model"] == model), None)
    if entry is None:
        raise ValueError(
            f"Unknown model {model!r}; valid names: {[entry['model'] for entry in CATALOG]}"
        )
    mask = MIPClient.from_env(
        entry["deployment"], **entry.get("preprocessing", {})
    ).segment(image_path, prompts)
    image = Path(image_path).resolve()
    image_stem = image.name.removesuffix(".gz").removesuffix(".nii")
    prompt_hash = hashlib.sha256(json.dumps(prompts).encode("utf-8")).hexdigest()[:8]
    stem = f"{model}-{prompt_hash}"
    # Mirror the repo path so same-named series from different exams stay apart.
    relative = image.parent.relative_to(REPO_ROOT).parts if image.is_relative_to(REPO_ROOT) else ()
    output_dir = AUDIT_DIR.joinpath(*relative, image_stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    mask_path = output_dir / f"{stem}.nii.gz"
    nib.save(mask, mask_path)
    (output_dir / f"{stem}.json").write_text(
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
    images = [
        figures.save_film_grid(image, output_dir / "film-grid.png", image.name),
        figures.save_film_grid(image, output_dir / f"{stem}.film-grid.png",
                               f"{image.name}: {model}", mask_path, prompts),
    ]
    labels = np.asanyarray(mask.dataobj)
    voxel_ml = abs(float(np.linalg.det(mask.affine[:3, :3]))) / 1000
    return {
        "audit_dir": str(output_dir),
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
        "images": images,
    }
