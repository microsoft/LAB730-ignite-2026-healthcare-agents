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


# TODO (Chapter 2): Register `segmentation.segment` as an MCP tool named `segment` here.


# TODO (Chapter 2): Register `lesions.clean_segmentation` as `clean_segmentation`.
# Follow the working wrapper above, using the function's signature and docstring.


# TODO (Chapter 2): Register `lesions.describe_lesions` as `describe_lesions`.
# Follow the same wrapper pattern; the lesions module is imported above.


if __name__ == "__main__":
    mcp.run(transport="stdio")
