"""Workshop environment check. Run: uv run workshop/check_env.py"""

import argparse
from importlib import import_module
from pathlib import Path
import sys
from time import perf_counter
from urllib.parse import urlsplit

for package in (
    "numpy", "pandas", "PIL", "sklearn", "dotenv", "requests", "matplotlib",
    "ipykernel", "nibabel", "SimpleITK", "scipy", "skimage", "tenacity", "mcp",
):
    try:
        import_module(package)
    except ImportError as exc:
        sys.exit(f"Missing package: {exc.name or package} (importing {package})")

import numpy as np
import requests
from tenacity import RetryError
from mip_client import MIPClient

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--deployment", default="mip3d-mri-brain-lesion")
deployment = parser.parse_args().deployment
try:
    client = MIPClient.from_env(deployment)
except RuntimeError as exc:
    sys.exit(str(exc))
print(f"Endpoint host: {urlsplit(client.endpoint).hostname}", flush=True)

sample = Path(__file__).resolve().parents[1] / (
    "samples/mri-brain-lesions/case-056/2018-04-14/series-0902.nii.gz"
)
if not sample.is_file() or sample.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1"):
    sys.exit("sample not downloaded: run git lfs pull")
started = perf_counter()
try:
    mask = client.segment(sample, ["post-contrast T1 MRI brain showing enhancing tumor"])
except (requests.exceptions.RequestException, RetryError) as exc:
    error = exc.last_attempt.exception() if isinstance(exc, RetryError) else exc
    if isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        sys.exit("Connection/timeout error: check network/endpoint URL")
    response = getattr(error, "response", None)
    status = response.status_code if response is not None else "unavailable"
    hint = {
        401: "; check MIP_MODEL_API_KEY", 403: "; check MIP_MODEL_API_KEY",
        404: "; check MIP_MODEL_ENDPOINT or the deployment name",
    }.get(status, "")
    sys.exit(f"HTTP {status}{hint}")
print(f"Endpoint OK: {perf_counter() - started:.2f}s; labels: {np.unique(mask.dataobj).tolist()}")
print(f"Workshop env OK — Python {sys.version_info.major}.{sys.version_info.minor}; endpoint OK ({deployment})")
