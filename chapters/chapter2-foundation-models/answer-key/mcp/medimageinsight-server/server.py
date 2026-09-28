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


@mcp.tool(description=zero_shot.classify.__doc__)
def zeroshot_classify(file_path: str, labels: list[str]) -> dict[str, float]:
    return zero_shot.classify(file_path, labels)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------
@mcp.tool(description=adapter.classify.__doc__)
def adapter_classify(file_path: str, head: str = "mlp") -> dict[str, str]:
    return adapter.classify(file_path, head=head)


if __name__ == "__main__":
    mcp.run(transport="stdio")
