# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""MedImageInsight MCP server.

Exposes MedImageInsight zero-shot classification as MCP tools.

Run with:
    uv run --directory <path-to-this-dir> mcp run server.py

Env vars (set in .env alongside this file, or in .vscode/mcp.json):
    MI2_MODEL_ENDPOINT    Full AML scoring URL for MedImageInsight.
    MI2_MODEL_API_KEY     Bearer token for the endpoint.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

import adapter
import zero_shot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("medimageinsight")


# ---------------------------------------------------------------------------
# Zero shot
# ---------------------------------------------------------------------------
@mcp.tool(description=zero_shot.label_examples.__doc__)
def zeroshot_label_examples(
    group: str | None = None,
    regex: str | None = None,
) -> list[str]:
    return zero_shot.label_examples(group=group, regex=regex)


# TODO (Chapter 2, Part 1): Register `zero_shot.classify` as an MCP tool here.


# ---------------------------------------------------------------------------
# Adapter 
# ---------------------------------------------------------------------------
# TODO (Chapter 2, Part 2): Add an `adapter_classify` wrapper that delegates to `adapter.classify`.
# Same pattern as `zeroshot_classify` above. The adapter module is imported above.


if __name__ == "__main__":
    mcp.run(transport="stdio")
