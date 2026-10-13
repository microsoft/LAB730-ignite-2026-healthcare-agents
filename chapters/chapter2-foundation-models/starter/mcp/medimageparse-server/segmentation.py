# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Prompt-based brain lesion segmentation with MedImageParse.

Keeps the MCP server thin: ``server.py`` registers tools, this module owns the
prompt catalog, the MedImageParse call, and where masks land on disk.

PLACEHOLDER (Ignite 2026): ``prompt_examples`` works today. ``segment`` defines
the tool contract (its docstring is the tool description the agent sees) but
raises ``NotImplementedError`` until the MedImageParse client in
``workshop/mip_client.py`` is implemented.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from workshop import mip_client  # noqa: F401  (used once segment() is implemented)

# Resolves to <workspace-root>/outputs/masks/ (parents[2] climbs out of mcp/medimageparse-server/).
MASKS_DIR = Path(__file__).resolve().parents[2] / "outputs" / "masks"


def segment(file_path: str, prompts: list[str]) -> dict[str, dict]:
    """Segment brain lesions in an MRI image with MedImageParse — one mask per text prompt.

    Prompts are short target names such as ``"enhancing tumor"`` or
    ``"edema"``. Send all prompts for an image in **one** call. Use the
    ``prompt_examples`` tool to discover prompts that suit the image's MRI
    sequence.

    Masks are saved to disk and returned as file paths — the pixels never go
    into the chat. Pass a ``mask_path`` to the ``measure_lesions`` tool to get
    laterality and sizes in millimeters.

    Args:
        file_path: **Absolute** path to an axial brain MRI image (PNG). A sidecar
            ``<image>.json`` with ``sequence`` and ``pixel_spacing_mm`` should sit
            next to it.
        prompts: Text prompts, one per target to segment.

    Returns:
        ``{prompt: {"detected": bool, "mask_path": str | None, "pixel_count": int, "category": str}}``

        - ``detected`` — True when the model returned a non-empty mask.
        - ``mask_path`` — absolute path of the saved mask PNG (``None`` when
          nothing was detected).
        - ``pixel_count`` — mask size in pixels. Not a physical size; do not
          convert it to millimeters.
        - ``category`` — the model's coarse category for the prompt
          (e.g. ``"tumor"``).
    """
    # TODO(mip): implement with MedImageParse. Planned steps:
    #   1. Read the image bytes and its sidecar JSON (sequence, pixel_spacing_mm).
    #   2. mip_client.segment(image_bytes, prompts) -> masks [n_prompts, 1024, 1024],
    #      categories, and the pad/resize geometry (one POST, prompts joined with " & ").
    #   3. Undo the pad/resize so every mask matches the original image grid —
    #      otherwise the sidecar pixel spacing no longer applies.
    #   4. Save each non-empty mask to MASKS_DIR / f"{stem}__{prompt_slug}.png" with a
    #      sidecar JSON {source_image, prompt, sequence, pixel_spacing_mm} for measure_lesions.
    #   5. Return the dict documented above.
    raise NotImplementedError(
        "TODO(mip): MedImageParse segmentation is not implemented yet (Ignite 2026 placeholder)."
    )


def prompt_examples(regex: str | None = None) -> list[dict[str, str]]:
    """List example MedImageParse text prompts for brain MRI lesions.

    Each entry has:

    - ``prompt`` — pass verbatim to ``segment_lesions``.
    - ``sequence`` — the MRI sequence the prompt suits (e.g. ``"T1-Gd"`` for
      post-contrast T1-weighted, ``"FLAIR"``). Match it to the ``sequence``
      field in the image's sidecar JSON.
    - ``target`` — what the resulting mask covers.

    Args:
        regex: Optional case-insensitive filter (Python ``re.search``) applied
            to ``prompt``, ``sequence``, and ``target``. Examples: ``"flair"``,
            ``"enhanc"``.

    Returns:
        A list of ``{"prompt", "sequence", "target"}`` dicts.
    """
    catalog_path = Path(__file__).with_name("prompt_examples.json")
    entries = json.loads(catalog_path.read_text(encoding="utf-8"))["prompts"]
    if not regex:
        return entries
    compiled = re.compile(regex, re.IGNORECASE)
    return [
        entry
        for entry in entries
        if any(compiled.search(entry.get(key, "")) for key in ("prompt", "sequence", "target"))
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MedImageParse brain lesion segmentation (standalone, bypasses MCP)."
    )
    parser.add_argument(
        "image",
        help="path to an axial brain MRI image (e.g., samples/SYN0417_003.png)",
    )
    parser.add_argument(
        "--prompts",
        nargs="+",
        default=["enhancing tumor", "non-enhancing tumor"],
        help="text prompts to segment (default: the post-contrast T1 set)",
    )
    args = parser.parse_args()

    results = segment(str(Path(args.image).resolve()), args.prompts)
    for prompt, result in results.items():
        print(f"{prompt:25s} {result}")
