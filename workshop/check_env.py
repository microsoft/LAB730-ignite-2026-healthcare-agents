"""Workshop environment check. Run: uv run workshop/check_env.py"""

import argparse
import logging
import os
import platform
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
import urllib3
from dotenv import find_dotenv
from tenacity import RetryError
from mip_client import MIPClient

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--deployment", default="mip3d-mri-brain-lesion")
parser.add_argument("--verbose", "-v", action="store_true", help="Show connection diagnostics")
args = parser.parse_args()
if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
env_file = os.environ.get("MIP_ENV_FILE")
try:
    client = MIPClient.from_env(args.deployment, timeout=60)
except RuntimeError as exc:
    sys.exit(str(exc))
print(f"Endpoint host: {urlsplit(client.endpoint).hostname}", flush=True)

sample = Path(__file__).resolve().parents[1] / (
    "samples/mri-brain-lesions/case-056/2018-04-14/series-0902.nii.gz"
)
if not sample.is_file() or sample.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1"):
    sys.exit("sample not downloaded: run git lfs pull")
if args.verbose:
    print(f"Python: {platform.python_version()}; platform: {platform.platform()}", flush=True)
    print(f"requests: {requests.__version__}; urllib3: {urllib3.__version__}", flush=True)
    print(f"Dotenv ({'MIP_ENV_FILE' if env_file else 'default search from workshop'}): {env_file or find_dotenv() or 'not found'}", flush=True)
    endpoint = urlsplit(client.endpoint)
    print(f"Endpoint: scheme={endpoint.scheme}; host={endpoint.hostname}; port={endpoint.port}; path={endpoint.path}", flush=True)
    print(f"Deployment: {args.deployment}; sample: {sample} ({sample.stat().st_size} bytes)", flush=True)
    names = ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE")
    print(f"Proxy/TLS variables set: {', '.join(name for name in names if name in os.environ) or 'none'}", flush=True)
started = perf_counter()
try:
    mask = client.segment(sample, ["post-contrast T1 MRI brain showing enhancing tumor"])
except (requests.exceptions.RequestException, RetryError) as exc:
    error = exc.last_attempt.exception() if isinstance(exc, RetryError) else exc
    response = getattr(error, "response", None)
    if args.verbose:
        print(f"Failed after {perf_counter() - started:.2f}s; attempts: {exc.last_attempt.attempt_number if isinstance(exc, RetryError) else client._post.statistics.get('attempt_number', 1)}", file=sys.stderr)
        pending, seen = [("Exception", exc)], set()
        while pending:
            label, current = pending.pop()
            if current is None or id(current) in seen:
                continue
            seen.add(id(current))
            print(f"{label}: {type(current).__name__}: {current}", file=sys.stderr)
            pending.extend([("Context", current.__context__), ("Cause", current.__cause__)])
            if isinstance(current, RetryError):
                pending.append(("Last attempt", current.last_attempt.exception()))
        if response is not None:
            print(f"HTTP response: {response.status_code} {response.reason}; body: {response.text[:500]!r}", file=sys.stderr)
    if isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        sys.exit(f"Cannot reach the endpoint ({type(error).__name__}): {error} (rerun with --verbose for details)")
    status = response.status_code if response is not None else "unavailable"
    hint = {
        401: "; check MIP_MODEL_API_KEY", 403: "; check MIP_MODEL_API_KEY",
        404: "; check MIP_MODEL_ENDPOINT or the deployment name",
    }.get(status, "")
    sys.exit(f"HTTP {status}{hint}")
print(f"Endpoint OK: {perf_counter() - started:.2f}s; labels: {np.unique(mask.dataobj).tolist()}")
print(f"Workshop env OK — Python {sys.version_info.major}.{sys.version_info.minor}; endpoint OK ({args.deployment})")
