# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""MedImageParse 3D client returning categorical uint8 masks on the source grid.

Requests contain gzipped NIfTI bytes and ampersand-separated prompts.
Slice-first predictions are unpadded and reoriented without resampling.
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import os
from pathlib import Path

import nibabel as nib
import numpy as np
import requests
from dotenv import load_dotenv
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

# Load .env: explicit MIP_ENV_FILE wins, else default dotenv search from CWD.
_env_file = os.environ.get("MIP_ENV_FILE")
if _env_file:
    load_dotenv(_env_file, override=False)
else:
    load_dotenv()

logger = logging.getLogger(__name__)

_DEPLOYMENTS = {
    "base": "MIP_DEPLOYMENT_BASE",
    "mri-brain-lesion": "MIP_DEPLOYMENT_MRI_BRAIN_LESION",
    "mri-brain-anatomy": "MIP_DEPLOYMENT_MRI_BRAIN_ANATOMY",
}


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, requests.exceptions.ConnectionError):
        return True
    if isinstance(exc, requests.exceptions.Timeout):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        code = exc.response.status_code if exc.response is not None else 0
        return code == 429 or 500 <= code < 600
    return False


_retry = retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_random_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)


@_retry
def _post(payload: dict, deployment: str) -> list:
    endpoint = os.environ.get("MIP_MODEL_ENDPOINT", "")
    key = os.environ.get("MIP_MODEL_API_KEY", "")
    if not endpoint or not key:
        raise RuntimeError(
            "MIP_MODEL_ENDPOINT and MIP_MODEL_API_KEY must be set "
            "(via .env file or environment)."
        )
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "azureml-model-deployment": deployment,
    }
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=300)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise requests.exceptions.HTTPError(
            f"MIP request failed with HTTP {exc.response.status_code}",
            response=exc.response,
        ) from None
    except requests.exceptions.RequestException as exc:
        raise type(exc)("MIP request failed") from None
    return resp.json()


def segment(nifti_path: str | Path, prompts: list[str], model: str) -> nib.Nifti1Image:
    """Return source-grid labels: 0 is background; label i matches prompts[i-1]."""
    if model not in _DEPLOYMENTS:
        raise ValueError(f"Unknown model; choose from {', '.join(_DEPLOYMENTS)}")
    deployment_var = _DEPLOYMENTS[model]
    deployment = os.environ.get(deployment_var, "").strip()
    if not deployment:
        raise RuntimeError(f"{deployment_var} must be set to a deployment name")
    if not 1 <= len(prompts) <= 255 or any(
        not prompt.strip() or "&" in prompt for prompt in prompts
    ):
        raise ValueError("Provide 1-255 nonempty prompts without '&' delimiters")

    source = nib.load(nifti_path)
    if len(source.shape) != 3:
        raise ValueError("Input must be a 3D NIfTI volume")
    source_orientation = nib.orientations.io_orientation(source.affine)
    target_orientation = nib.orientations.axcodes2ornt(
        ("P", "L", "S") if model == "mri-brain-anatomy" else ("R", "A", "S")
    )
    transform = nib.orientations.ornt_transform(source_orientation, target_orientation)
    oriented = source.as_reoriented(transform)
    values = np.asarray(oriented.dataobj, dtype=np.float32)
    if not np.isfinite(values).all() or values.max() <= 0:
        raise ValueError("Input intensities must be finite with some positive voxels")
    upper = (
        float(values.max())
        if model == "mri-brain-anatomy"
        else np.percentile(values[values > 0], 99.5)
    )
    scaled = (np.clip(values, 0, upper) / upper * 255).astype(np.uint8)
    padding = [(0, 0)] * 3
    if model == "mri-brain-anatomy":
        side = max(256, *scaled.shape[:2])
        padding = [
            ((side - size) // 2, (side - size + 1) // 2)
            for size in scaled.shape[:2]
        ] + [(0, 0)]
    prepared = np.pad(scaled, padding)
    affine = oriented.affine.copy()
    affine[:3, 3] -= affine[:3, :3] @ np.array([pair[0] for pair in padding])
    image_bytes = gzip.compress(nib.Nifti1Image(prepared, affine).to_bytes())
    payload = {
        "input_data": {
            "columns": ["image", "text"],
            "index": [0],
            "data": [[base64.b64encode(image_bytes).decode(), "&".join(prompts)]],
        }
    }
    response = _post(payload, deployment)
    encoded = json.loads(response[0]["nifti_file"])["data"]
    prediction = nib.Nifti1Image.from_bytes(gzip.decompress(base64.b64decode(encoded)))
    labels = np.asanyarray(prediction.dataobj)
    if labels.shape != (prepared.shape[2], *prepared.shape[:2]):
        raise ValueError(f"Unexpected endpoint mask shape: {labels.shape}")
    if (
        not np.isfinite(labels).all()
        or not np.equal(labels, np.rint(labels)).all()
        or labels.min() < 0
        or labels.max() > len(prompts)
    ):
        raise ValueError("Endpoint mask must contain categorical IDs in the prompt range")
    # Endpoint affines are stale; invert the preparation geometry instead.
    interior = tuple(
        slice(pair[0], pair[0] + length)
        for pair, length in zip(padding, oriented.shape)
    )
    cropped = labels.astype(np.uint8).transpose(1, 2, 0)[interior]
    inverse = nib.orientations.ornt_transform(target_orientation, source_orientation)
    restored = nib.orientations.apply_orientation(cropped, inverse)
    if restored.shape != source.shape:
        raise ValueError("Prediction could not be restored to the source grid")
    header = source.header.copy()
    header.set_data_dtype(np.uint8)
    return nib.Nifti1Image(restored, source.affine, header)
