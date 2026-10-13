# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Physical measurements of connected components in a 3D NIfTI mask."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage


def measure(mask_path: str, label: int, min_volume_ml: float = 0.1) -> dict:
    """Measure one foreground label in a mask returned by segment.

    Uses full 3D (26-neighbor) connectivity and drops components smaller than
    min_volume_ml. Returns label, its prompt, total_volume_ml of retained
    components, component_count, and components sorted largest first.
    Each component has volume_ml, extent_cm (AP, TR, CC), and centroid_ras_mm
    (right, anterior, superior world coordinates). Values use one decimal.
    Extents are voxel bounding boxes after canonical RAS reorientation, not
    longest lesion diameters; oblique images retain their voxel-axis tilt.
    NIfTI geometry must be in millimeters. No laterality is inferred.
    """
    if not np.isfinite(min_volume_ml) or min_volume_ml < 0:
        raise ValueError("min_volume_ml must be finite and nonnegative")
    path = Path(mask_path)
    stem = path.name.removesuffix(".gz").removesuffix(".nii")
    metadata = json.loads(path.with_name(f"{stem}.json").read_text(encoding="utf-8"))
    if not 1 <= label <= len(metadata["prompts"]):
        raise ValueError("label must be a foreground ID from the mask's prompts")
    mask = nib.as_closest_canonical(nib.load(path))
    regions, _ = ndimage.label(
        np.asanyarray(mask.dataobj) == label, structure=np.ones((3, 3, 3), dtype=bool)
    )
    counts = np.bincount(regions.ravel())
    boxes = ndimage.find_objects(regions)
    voxel_ml = abs(float(np.linalg.det(mask.affine[:3, :3]))) / 1000
    voxel_sizes = nib.affines.voxel_sizes(mask.affine)
    components = []
    total_volume_ml = 0.0
    for region_id in sorted(
        range(1, len(counts)), key=lambda region_id: -counts[region_id]
    ):
        volume_ml = float(counts[region_id]) * voxel_ml
        if volume_ml < min_volume_ml:
            continue
        box = boxes[region_id - 1]
        lengths = np.array([axis.stop - axis.start for axis in box])
        extent_cm = lengths * voxel_sizes / 10
        centroid = np.argwhere(regions[box] == region_id).mean(axis=0)
        centroid += np.array([axis.start for axis in box])
        centroid_ras_mm = nib.affines.apply_affine(mask.affine, centroid)
        components.append(
            {
                "volume_ml": round(volume_ml, 1),
                "extent_cm": {
                    "AP": round(float(extent_cm[1]), 1),
                    "TR": round(float(extent_cm[0]), 1),
                    "CC": round(float(extent_cm[2]), 1),
                },
                "centroid_ras_mm": [
                    round(float(value), 1) for value in centroid_ras_mm
                ],
            }
        )
        total_volume_ml += volume_ml
    return {
        "label": label,
        "prompt": metadata["prompts"][label - 1],
        "total_volume_ml": round(total_volume_ml, 1),
        "component_count": len(components),
        "components": components,
    }
