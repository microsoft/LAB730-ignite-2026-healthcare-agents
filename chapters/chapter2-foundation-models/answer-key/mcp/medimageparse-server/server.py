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


@mcp.tool(description=segmentation.segment.__doc__)
def segment(image_path: str, model: str, prompts: list[str]) -> dict:
    return segmentation.segment(image_path, model, prompts)


@mcp.tool(description=measurement.measure.__doc__)
def measure(mask_path: str, label: int, min_volume_ml: float = 0.1) -> dict:
    return measurement.measure(mask_path, label, min_volume_ml)


if __name__ == "__main__":
    mcp.run(transport="stdio")
