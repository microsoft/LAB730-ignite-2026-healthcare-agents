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


@mcp.tool(description=segmentation.segment.__doc__)
def segment_lesions(file_path: str, prompts: list[str]) -> dict[str, dict]:
    return segmentation.segment(file_path, prompts)


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------
@mcp.tool(description=measurement.measure.__doc__)
def measure_lesions(mask_path: str) -> dict:
    return measurement.measure(mask_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
