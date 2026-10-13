# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""MedImageParse MCP server.

Exposes a model catalog, 3D segmentation, and component measurements as tools.
Deployment names and client preprocessing options come from models.json.

Run with:
    uv run --directory <path-to-this-dir> mcp run server.py

Env vars (set in .env alongside this file, or in .vscode/mcp.json):
    MIP_MODEL_ENDPOINT    Full scoring URL for the MedImageParse endpoint.
    MIP_MODEL_API_KEY     API key for the endpoint.
"""

from __future__ import annotations

import logging

import measurement
import segmentation
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("medimageparse")


@mcp.tool(description=segmentation.list_models.__doc__)
def list_models() -> list[dict]:
    return segmentation.list_models()


# TODO (Chapter 2, Part 1): Register `segmentation.segment` as an MCP tool named `segment` here.


# TODO (Chapter 2, Part 2): Add a `measure` wrapper that delegates to `measurement.measure`.
# Same pattern as `segment` above. The measurement module is imported above.


if __name__ == "__main__":
    mcp.run(transport="stdio")
