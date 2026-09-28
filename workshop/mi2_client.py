# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import logging
import os
from io import BytesIO

import numpy as np
import requests
from dotenv import load_dotenv
from PIL import Image
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

# Load .env: explicit MI2_ENV_FILE wins, else default dotenv search from CWD.
_env_file = os.environ.get("MI2_ENV_FILE")
if _env_file:
    load_dotenv(_env_file, override=False)
else:
    load_dotenv()

logger = logging.getLogger(__name__)


def preprocess_image(
    image_bytes: bytes,
    image_format: str = "JPEG",
    jpeg_quality: int = 75,
    resize_to: int = 512,
    normalize_percentiles: tuple[float, float] | None = (5.0, 95.0),
    passthrough_if_jpeg: bool = False,
) -> str:
    """PIL pipeline -> base64 string. All knobs exposed as kwargs.

    Defaults are calibrated for the workshop endpoint: JPEG@75, 512px,
    5-95 percentile clip. Tune via kwargs for other deployments.

    image_format          PNG | JPEG  (JPEG@75 matches MI2 training distribution)
    jpeg_quality          1-95, only used when format=JPEG
    resize_to             square edge size in pixels
    normalize_percentiles (lo, hi) percentile clip + rescale to 0-255.
                          None = skip (matches default for uint8 inputs).
    passthrough_if_jpeg   if True and the input bytes are already a JPEG
                          (magic 0xFFD8FF), return base64 of the raw bytes
                          unchanged - skips resize, normalize, and re-encode.
                          Use for inputs that are already preprocessed at the
                          target resolution/quality (e.g. JPG@95 518px).
    """
    if passthrough_if_jpeg and image_bytes[:3] == b"\xff\xd8\xff":
        return base64.b64encode(image_bytes).decode("ascii")

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((resize_to, resize_to), Image.BICUBIC)

    if normalize_percentiles is not None:
        arr = np.asarray(img).astype(np.float32)
        lo, hi = np.percentile(arr, normalize_percentiles)
        arr = np.clip((arr - lo) / max(hi - lo, 1e-6) * 255.0, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    buf = BytesIO()
    fmt = image_format.upper()
    if fmt == "JPEG":
        img.save(buf, format="JPEG", quality=jpeg_quality)
    else:
        img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("ascii")



def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, requests.exceptions.ConnectionError):
        return True
    if isinstance(exc, requests.exceptions.Timeout):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        code = exc.response.status_code if exc.response else 0
        return code == 429 or 500 <= code < 600
    return False


_retry = retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_random_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)


@_retry
def _score(rows: list) -> dict:
    endpoint = os.environ.get("MI2_MODEL_ENDPOINT", "")
    key = os.environ.get("MI2_MODEL_API_KEY", "")
    if not endpoint or not key:
        raise RuntimeError(
            "MI2_MODEL_ENDPOINT and MI2_MODEL_API_KEY must be set "
            "(via .env file or environment)."
        )
    payload = {
        "input_data": {
            "columns": ["image", "text"],
            "index": list(range(len(rows))),
            "data": rows,
        },
        "params": {},
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()


def get_embedding(image_bytes: bytes, **preprocess_kwargs) -> list[float]:
    """Single POST for image embedding. Returns 1-D feature vector as list[float].

    Extra kwargs are forwarded to preprocess_image (image_format, jpeg_quality,
    resize_to, normalize_percentiles).
    """
    b64 = preprocess_image(image_bytes, **preprocess_kwargs)
    result = _score([[b64, None]])  # list of one row
    feats = np.squeeze(np.array(result[0]["image_features"]))
    return feats.tolist()