---
name: write-report-measured
description: Write a brain MRI report grounded in MedImageParse lesion segmentation AND tool-computed lesion measurements (patient side, diameters in mm). Invoke whenever drafting a brain MRI report when both the `segment_lesions` and `measure_lesions` tools are available — preferred over `write-report-segmentation`.
argument-hint: |
  - image_path: required path to the brain MRI image (axial slice, PNG)
  - extra_prompts: optional list of additional MedImageParse text prompts to segment alongside the default set
---

# write-report-measured

Three-step skill: (1) segment brain lesions with MedImageParse, (2) measure the primary lesion mask with code, then (3) hand findings **and** measurements off to the existing `write-report-simple` skill. The model finds the lesion, code sizes it, and the LLM only writes the words. The report itself never mentions MedImageParse, masks, or any tool.

## Budget

- Tool calls: 2 — one `mcp_medimageparse_segment_lesions` call, then one `mcp_medimageparse_measure_lesions` call on the primary target's mask. Skip the measurement call when nothing was detected.
- Output: ≤ 200 words for the full report.
- Do not re-invoke skills already used in this turn.
- Do not retry tool calls on success.

## How to use

1. **Resolve the image to an absolute path.** The MCP tools run in a different working directory than the agent. If `image_path` is not absolute, resolve it (e.g. via `realpath`) before calling the tool. If you can't resolve it, ask the user.

2. **Segment.** Pick the prompt set for the image's sequence (the `sequence` field in the sidecar JSON next to the image) from [`../write-report-segmentation/references/prompts.md`](../write-report-segmentation/references/prompts.md), append any `extra_prompts`, and call `mcp_medimageparse_segment_lesions` once with the **absolute** path and the full list.

3. **Measure.** The primary target is the first prompt in the set. If it came back `detected: true`, call `mcp_medimageparse_measure_lesions` with its `mask_path`. The tool returns `lesion_count` and, per lesion (largest first), `side`, `longest_diameter_mm`, `perpendicular_diameter_mm`, and `area_mm2`.

4. **Hand off to `write-report-simple`.** Invoke the `write-report-simple` skill (already in the workspace skill drawer at `.github/skills/write-report-simple/`). Pass:
   - `findings`: one entry per prompt — `present` when `detected` is true, `absent` when false — with the tool's `side` for location wording.
   - `measurements`: the measured lesions **verbatim**, e.g. `enhancing tumor, lesion 1: {side}, {longest} × {perpendicular} mm (longest × perpendicular)`.

   The downstream skill copies measurements into the report as given.

5. **Return what `write-report-simple` returns.** Do not re-wrap, re-format, or annotate the report. The downstream skill emits the `<confidence>` and `<report>` blocks; pass them through unchanged.

## Critical rules

- **Numbers come from `measure_lesions` only.** Copy diameters verbatim — do not re-round, recompute, add, or convert units.
- **Laterality comes from the tool.** `side` is already the patient's side; the radiological display convention is handled in code. If your read of the image disagrees, trust the tool.
- **Several lesions:** when `lesion_count` > 1, give the largest lesion's dimensions and state how many additional lesions there are.
- **The report must not mention MedImageParse, masks, prompts, or any tool output.** If you want to attribute or caveat the tools in the chat reply *outside* the `<report>` tags, that's fine.
