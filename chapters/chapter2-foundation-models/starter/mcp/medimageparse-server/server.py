# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""MedImageParse MCP server.

Exposes MedImageParse brain lesion segmentation — and a measurement tool that
turns lesion masks into millimeters — as MCP tools.

Run with:
    uv run --directory <path-to-this-dir> mcp run server.py

Env vars (set in .env alongside this file, or in .vscode/mcp.json):
    MIP_MODEL_ENDPOINT    Full scoring URL for the MedImageParse deployment.
    MIP_MODEL_API_KEY     API key for the endpoint.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

import measurement
import segmentation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("medimageparse")


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------
@mcp.tool(description=segmentation.prompt_examples.__doc__)
def prompt_examples(regex: str | None = None) -> list[dict[str, str]]:
    return segmentation.prompt_examples(regex=regex)


# TODO (Chapter 2, Part 1): Register `segmentation.segment` as an MCP tool named `segment_lesions` here.


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------
# TODO (Chapter 2, Part 2): Add a `measure_lesions` wrapper that delegates to `measurement.measure`.
# Same pattern as `segment_lesions` above. The measurement module is imported above.


if __name__ == "__main__":
    mcp.run(transport="stdio")
