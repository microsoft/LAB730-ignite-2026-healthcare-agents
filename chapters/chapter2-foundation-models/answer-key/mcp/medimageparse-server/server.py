# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""MedImageParse MCP server.

Exposes a model catalog, 3D segmentation, lesion cleaning, and descriptors.
Deployment names and client preprocessing options come from models.json.

Run with:
    uv run --directory <path-to-this-dir> mcp run server.py

Env vars (from .env at the repository root, or the environment):
    MIP_MODEL_ENDPOINT    Full scoring URL for the MedImageParse endpoint.
    MIP_MODEL_API_KEY     API key for the endpoint.
"""

from __future__ import annotations

import logging

import lesions
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


@mcp.tool(description=lesions.clean_segmentation.__doc__)
def clean_segmentation(mask_path: str, merge_distance_mm: float = 5.0,
                       min_lesion_ml: float = 0.1, min_edema_ml: float = 0.1) -> dict:
    return lesions.clean_segmentation(mask_path, merge_distance_mm, min_lesion_ml, min_edema_ml)


@mcp.tool(description=lesions.describe_lesions.__doc__)
def describe_lesions(clean_path: str, prior_clean_path: str | None = None) -> dict:
    return lesions.describe_lesions(clean_path, prior_clean_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
