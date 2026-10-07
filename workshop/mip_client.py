# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Thin client for a MedImageParse (MIP) online endpoint.

PLACEHOLDER (Ignite 2026): the request plumbing (env loading, auth, retries)
is in place; the MedImageParse-specific pieces — preprocessing, request
payload, and mask decoding — are stubs marked ``TODO(mip)``.

Endpoint contract (MedImageParse, 2D), per
https://learn.microsoft.com/azure/ai-foundry/how-to/healthcare-ai/deploy-medimageparse

- Request: ``{"input_data": {"columns": ["image", "text"], "index": [0],
  "data": [[<base64 PNG, 1024x1024>, "prompt one & prompt two"]]}}``
- Response: ``[{"image_features": "<JSON string: {data: base64 ndarray,
  shape: [n_prompts, 1024, 1024], dtype}>", "text_features": [<category per prompt>]}]``
"""

from __future__ import annotations

import logging
import os

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

# MedImageParse expects square 1024x1024 inputs; masks come back on the same grid.
INPUT_SIZE = 1024


def preprocess_image(image_bytes: bytes) -> tuple[str, dict]:
    """Pad to square with black pixels, resize to 1024x1024 RGB PNG, base64-encode.

    Returns the base64 string plus the geometry needed to map masks back onto
    the original image grid (original size, scale factor, padding offsets).
    """
    # TODO(mip): implement — see the "Generating Segmentation for a Variety of
    # Imaging Modalities" sample notebook (https://aka.ms/healthcare-ai-examples-mip-examples).
    raise NotImplementedError("TODO(mip): MedImageParse preprocessing is not implemented yet.")


def decode_masks(image_features: str) -> np.ndarray:
    """Decode a response's ``image_features`` JSON string into a uint8 array
    of shape ``[n_prompts, 1024, 1024]``."""
    # TODO(mip): json.loads -> base64-decode "data" -> np.frombuffer(dtype).reshape(shape).
    raise NotImplementedError("TODO(mip): MedImageParse mask decoding is not implemented yet.")


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
def _post(payload: dict) -> list:
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
    }
    resp = requests.post(endpoint, json=payload, headers=headers, timeout=300)
    resp.raise_for_status()
    return resp.json()


def segment(image_bytes: bytes, prompts: list[str]) -> tuple[np.ndarray, list[str], dict]:
    """One MedImageParse call for all prompts.

    Returns ``(masks, categories, geometry)``: masks on the 1024x1024 model
    grid (one per prompt), the model's category per prompt, and the
    preprocessing geometry from ``preprocess_image`` for mapping masks back.
    """
    # TODO(mip): b64, geometry = preprocess_image(image_bytes)
    #            payload = {"input_data": {"columns": ["image", "text"], "index": [0],
    #                                      "data": [[b64, " & ".join(prompts)]]}}
    #            result = _post(payload)[0]
    #            return decode_masks(result["image_features"]), result["text_features"], geometry
    raise NotImplementedError("TODO(mip): MedImageParse segmentation is not implemented yet.")
