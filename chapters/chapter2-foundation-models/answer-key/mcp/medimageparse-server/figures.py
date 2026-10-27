# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Review images for people: axial montages and lesion measurement slices.

Radiological display: anterior up, patient right on screen left. Tile titles
give the zero-based RAS-canonical slice index (z) used by the descriptors.
"""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from matplotlib import colormaps
from matplotlib.figure import Figure
from matplotlib.patches import Patch

MAX_SLICES = 30
COLORS = colormaps["Set1"].colors
TEXT = {"color": "white", "fontsize": 10}


def _canonical(path):
    image = nib.as_closest_canonical(nib.load(path))
    return np.asarray(image.dataobj), nib.affines.voxel_sizes(image.affine)


def _show(axes, image, spacing, z, window, labels=None):
    # Rows run anterior to posterior; columns run patient right to left.
    aspect = spacing[1] / spacing[0]
    axes.imshow(image[:, :, z].T[::-1, ::-1], cmap="gray", vmin=window[0], vmax=window[1], aspect=aspect)
    if labels is not None:
        plane = labels[:, :, z].T[::-1, ::-1].astype(int)
        overlay = np.zeros((*plane.shape, 4))
        for value in np.unique(plane[plane > 0]):
            overlay[plane == value] = (*COLORS[(value - 1) % len(COLORS)], 0.45)
        axes.imshow(overlay, aspect=aspect)
    axes.set_axis_off()


def _figure(count, columns, size, title, names):
    rows = -(-count // columns)
    figure = Figure(figsize=(columns * size, rows * size + 1 + 0.3 * len(names)), facecolor="black", layout="constrained")
    grid = figure.subplots(rows, columns, squeeze=False).ravel()
    for axes in grid:
        axes.set_axis_off()
    figure.suptitle(f"{title}\nAxial, patient right on screen left", **TEXT)
    if names:
        handles = [Patch(color=COLORS[index % len(COLORS)], label=name) for index, name in enumerate(names)]
        figure.legend(handles=handles, loc="outside lower center", frameon=False, labelcolor="white")
    return figure, grid


def save_axial_montage(image_path, output_path, title, mask_path=None, names=()):
    """Save up to 30 evenly spaced axial slices; names[i] labels mask value i+1."""
    image, spacing = _canonical(image_path)
    labels = None if mask_path is None else _canonical(mask_path)[0]
    window = np.percentile(image[image > 0], [0.5, 99.5])
    slices = np.unique(np.linspace(0, image.shape[2] - 1, min(image.shape[2], MAX_SLICES)).round().astype(int))
    figure, grid = _figure(len(slices), 6, 2.5, title, names)
    for axes, z in zip(grid, slices):
        _show(axes, image, spacing, z, window, labels)
        axes.set_title(f"z {z}", **TEXT)
    figure.savefig(output_path, dpi=100)
    return str(output_path)


def save_measurements(descriptors, output_path):
    """Save each lesion's bidimensional slice with both diameters drawn; None without lesions."""
    records = [record for record in descriptors["descriptors"] if record["name"] == "bidimensional"]
    if not records:
        return None
    inputs, roles = descriptors["inputs"], descriptors["rules"]["labels"]
    image, spacing = _canonical(inputs["image_path"])
    labels = _canonical(inputs["clean_path"])[0]
    window = np.percentile(image[image > 0], [0.5, 99.5])
    title = f"{Path(inputs['image_path']).name}: bidimensional measurements (geometric proxy)"
    figure, grid = _figure(len(records), min(len(records), 3), 5, title, sorted(roles, key=roles.get))
    for axes, record in zip(grid, records):
        _show(axes, image, spacing, record["slice_index"], window, labels)
        for segment in record["segments_canonical_voxels"]:
            x, y, _ = np.array(segment).T
            axes.plot(image.shape[0] - 1 - x, image.shape[1] - 1 - y, color="yellow", linewidth=1.5)
        long_cm, short_cm = record["diameters_cm"]
        axes.set_title(f"{record['lesion']}, z {record['slice_index']}: {long_cm} x {short_cm} cm", **TEXT)
    figure.savefig(output_path, dpi=100)
    return str(output_path)
