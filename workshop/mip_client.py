# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Configurable MedImageParse 3D client returning source-grid uint8 masks."""

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

logger = logging.getLogger(__name__)


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


class MIPClient:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment_name: str | None = None,
        *,
        orientation: str = "RAS",
        upper_percentile: float = 99.5,
        pad_to: int | None = None,
        timeout: float = 300,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.orientation = orientation
        self.upper_percentile = upper_percentile
        self.pad_to = pad_to
        self.timeout = timeout

    @classmethod
    def from_env(
        cls, deployment_name: str | None = None, **options
    ) -> "MIPClient":
        load_dotenv(os.environ.get("MIP_ENV_FILE") or None, override=False)
        return cls(
            os.environ["MIP_MODEL_ENDPOINT"],
            os.environ["MIP_MODEL_API_KEY"],
            deployment_name,
            **options,
        )

    @_retry
    def _post(self, payload: dict, deployment: str) -> list:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "azureml-model-deployment": deployment,
        }
        try:
            resp = requests.post(
                self.endpoint, json=payload, headers=headers, timeout=self.timeout
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise requests.exceptions.HTTPError(
                f"MIP request failed with HTTP {exc.response.status_code}",
                response=exc.response,
            ) from None
        except requests.exceptions.RequestException as exc:
            raise type(exc)("MIP request failed") from None
        return resp.json()

    def _prepare(self, source: nib.Nifti1Image):
        source_orientation = nib.orientations.io_orientation(source.affine)
        target_orientation = nib.orientations.axcodes2ornt(self.orientation)
        transform = nib.orientations.ornt_transform(source_orientation, target_orientation)
        oriented = source.as_reoriented(transform)
        values = np.asarray(oriented.dataobj, dtype=np.float32)
        positive = values[values > 0]
        upper = np.percentile(positive, self.upper_percentile) if positive.size else 1
        scaled = (np.clip(values, 0, upper) / upper * 255).astype(np.uint8)
        padding = [(0, 0)] * 3
        if self.pad_to is not None:
            side = max(self.pad_to, *scaled.shape[:2])
            padding = [
                ((side - size) // 2, (side - size + 1) // 2)
                for size in scaled.shape[:2]
            ] + [(0, 0)]
        prepared = np.pad(scaled, padding)
        affine = oriented.affine.copy()
        affine[:3, 3] -= affine[:3, :3] @ np.array([pair[0] for pair in padding])
        interior = tuple(
            slice(pair[0], pair[0] + length)
            for pair, length in zip(padding, oriented.shape)
        )
        return nib.Nifti1Image(prepared, affine), interior

    @staticmethod
    def _restore(prediction, source, prepared, interior) -> nib.Nifti1Image:
        labels = np.asanyarray(prediction.dataobj)
        if labels.shape != (prepared.shape[2], *prepared.shape[:2]):
            raise ValueError(f"Unexpected endpoint mask shape: {labels.shape}")
        # Endpoint affines are stale; invert the preparation geometry instead.
        cropped = labels.astype(np.uint8).transpose(1, 2, 0)[interior]
        inverse = nib.orientations.ornt_transform(
            nib.orientations.io_orientation(prepared.affine),
            nib.orientations.io_orientation(source.affine),
        )
        restored = nib.orientations.apply_orientation(cropped, inverse)
        header = source.header.copy()
        header.set_data_dtype(np.uint8)
        return nib.Nifti1Image(restored, source.affine, header)

    def segment(
        self,
        image_path: str | Path,
        prompts: list[str],
        *,
        deployment_name: str | None = None,
    ) -> nib.Nifti1Image:
        """Return source-grid labels: 0 is background; label i matches prompts[i-1]."""
        if not prompts or any(not prompt.strip() or "&" in prompt for prompt in prompts):
            raise ValueError("Provide nonempty prompts without '&' delimiters")
        deployment = self.deployment_name if deployment_name is None else deployment_name
        source = nib.load(image_path)
        prepared, interior = self._prepare(source)
        image_bytes = gzip.compress(prepared.to_bytes())
        payload = {
            "input_data": {
                "columns": ["image", "text"],
                "index": [0],
                "data": [[base64.b64encode(image_bytes).decode(), "&".join(prompts)]],
            }
        }
        response = self._post(payload, deployment)
        encoded = json.loads(response[0]["nifti_file"])["data"]
        prediction = nib.Nifti1Image.from_bytes(gzip.decompress(base64.b64decode(encoded)))
        return self._restore(prediction, source, prepared, interior)
