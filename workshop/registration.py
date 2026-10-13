"""Look up precomputed transforms and resample labels onto a reference grid."""

from __future__ import annotations

from functools import cache
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import nibabel as nib
import numpy as np
import SimpleITK as sitk


_SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@cache
def _load_index() -> dict[tuple[str, str], Path]:
    with (_SAMPLES / "registrations.json").open() as stream:
        entries = json.load(stream)
    return {
        (entry["moving_sha256"], entry["reference_sha256"]): _SAMPLES / entry["transform"]
        for entry in entries
    }


def find_transform(moving_path: str | Path, reference_path: str | Path) -> Path:
    """Find the ordered pair by file SHA-256; raise LookupError if it is absent."""
    with Path(moving_path).open("rb") as moving, Path(reference_path).open("rb") as reference:
        hashes = (
            hashlib.file_digest(moving, "sha256").hexdigest(),
            hashlib.file_digest(reference, "sha256").hexdigest(),
        )
    try:
        transform_path = _load_index()[hashes]
    except KeyError:
        raise LookupError(
            f"No precomputed transform for moving file '{moving_path}' "
            f"and reference file '{reference_path}'."
        ) from None
    if not transform_path.is_file():
        raise FileNotFoundError(f"Precomputed transform is missing: {transform_path}")
    return transform_path


def resample_mask(
    mask: nib.Nifti1Image,
    moving_path: str | Path,
    reference_path: str | Path,
) -> nib.Nifti1Image:
    """Resample moving-grid labels with nearest neighbour, zero fill and uint8 output."""
    transform_path = find_transform(moving_path, reference_path)
    moving = nib.load(moving_path)
    reference = nib.load(reference_path)
    if len(moving.shape) != 3 or len(reference.shape) != 3:
        raise ValueError("Moving and reference series must be 3D NIfTI volumes")
    if mask.shape != moving.shape or not np.allclose(
        mask.affine, moving.affine, rtol=0, atol=1e-4
    ):
        raise ValueError("Mask must be on the moving series grid")
    values = np.asanyarray(mask.dataobj)
    if (
        not np.isfinite(values).all()
        or not np.equal(values, np.rint(values)).all()
        or values.min() < 0
        or values.max() > 255
    ):
        raise ValueError("Mask must contain integer labels in the range 0-255")
    with TemporaryDirectory() as directory:
        mask_path = Path(directory) / "mask.nii"
        output_path = Path(directory) / "resampled.nii"
        nib.save(mask, mask_path)
        resampled = sitk.Resample(
            sitk.ReadImage(str(mask_path), sitk.sitkUInt8),
            sitk.ReadImage(str(reference_path)),
            sitk.ReadTransform(str(transform_path)),
            sitk.sitkNearestNeighbor,
            0,
            sitk.sitkUInt8,
        )
        sitk.WriteImage(resampled, str(output_path))
        labels = np.array(nib.load(output_path).dataobj, dtype=np.uint8, copy=True)
    header = reference.header.copy()
    header.set_data_dtype(np.uint8)
    return nib.Nifti1Image(labels, reference.affine, header)