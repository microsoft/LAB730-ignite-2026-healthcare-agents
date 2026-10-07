# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Lesion measurements from a MedImageParse mask.

Plain geometry, no model call: the segmentation model decides *which* pixels
are lesion; this module turns those pixels into facts a report can use —
laterality and size in millimeters.

PLACEHOLDER (Ignite 2026): ``measure`` defines the tool contract (its docstring
is the tool description the agent sees) but raises ``NotImplementedError``
until the measurement code is implemented.
"""
from __future__ import annotations


def measure(mask_path: str) -> dict:
    """Measure the lesions in a segmentation mask: patient side and size in millimeters.

    Each connected region of the mask is one lesion. Pixel spacing comes from
    the mask's sidecar JSON (written by ``segment_lesions``), so sizes are real
    millimeters. Sizes follow the bidimensional convention used for brain
    tumors on axial images: the longest in-plane diameter, and the longest
    diameter perpendicular to it.

    Args:
        mask_path: Path to a mask returned by ``segment_lesions`` (its
            ``mask_path`` field).

    Returns:
        ``{"prompt": str, "pixel_spacing_mm": [float, float], "lesion_count": int, "lesions": [...]}``

        ``lesions`` is sorted largest first. Each lesion is
        ``{"side": "left" | "right" | "midline", "longest_diameter_mm": int,
        "perpendicular_diameter_mm": int, "area_mm2": int}``.

        - ``side`` is the **patient's** side — the radiological display
          convention (patient right on image left) is already handled.
        - Values are rounded to whole millimeters. Report them verbatim; do not
          recompute, re-round, or convert units.
    """
    # TODO(mip): implement. Planned steps:
    #   1. Load the mask PNG as a boolean array and its sidecar JSON
    #      (prompt, pixel_spacing_mm as [row_mm, col_mm], source image).
    #   2. Label connected components (e.g. scipy.ndimage.label); drop specks below a
    #      minimum area. Add scipy / scikit-image to pyproject.toml if used directly.
    #   3. Per component: area_mm2 = pixel count * row_mm * col_mm; longest diameter =
    #      max distance between boundary points (in mm); perpendicular diameter =
    #      longest extent orthogonal to it.
    #   4. side: component centroid vs. the image midline column. The image-left half
    #      is the patient's RIGHT (radiological convention); "midline" within a margin.
    #   5. Sort by area, round, and return the dict documented above.
    raise NotImplementedError(
        "TODO(mip): lesion measurement is not implemented yet (Ignite 2026 placeholder)."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Measure lesions in a segmentation mask (standalone, bypasses MCP)."
    )
    parser.add_argument(
        "mask",
        help="path to a mask written by segment_lesions (e.g., outputs/masks/SYN0417_003__enhancing-tumor.png)",
    )
    args = parser.parse_args()

    result = measure(args.mask)
    for lesion in result["lesions"]:
        print(lesion)
