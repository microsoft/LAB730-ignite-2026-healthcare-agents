---
name: write-report-segmentation
description: Write a brain MRI report grounded in MedImageParse lesion segmentation. Invoke whenever drafting a brain MRI report when the MedImageParse `segment_lesions` tool is available but `measure_lesions` is not — get mask-backed lesion findings, then delegate the prose to `write-report-simple`.
argument-hint: |
  - image_path: required path to the brain MRI image (axial slice, PNG)
  - extra_prompts: optional list of additional MedImageParse text prompts to segment alongside the default set
---

# write-report-segmentation

Two-step skill: (1) call MedImageParse to segment brain lesions in the image, then (2) hand the mask-backed findings off to the existing `write-report-simple` skill to produce the actual report. The report itself never mentions MedImageParse, masks, or prompts — it reads as the radiologist's direct read of the image.

## Budget

- Tool calls: 1 — exactly one `mcp_medimageparse_segment_lesions` call per image, with all prompts in that call.
- Output: ≤ 200 words for the full report.
- Do not re-invoke skills already used in this turn.
- Do not retry tool calls on success.

## How to use

1. **Resolve the image to an absolute path.** The MCP tool runs in a different working directory than the agent. If `image_path` is not absolute, resolve it (e.g. via `realpath`) before calling the tool. If you can't resolve it, ask the user.

2. **Pick the prompts.**
   - Read the sidecar JSON next to the image (same name, `.json` extension) and note its `sequence` (e.g. `T1-Gd`, `FLAIR`). If there is no sidecar, use the default set.
   - Take the prompt set for that sequence from [`references/prompts.md`](references/prompts.md) and use the strings **verbatim**.
   - If the caller provided `extra_prompts`, append them.

3. **Segment.** Call `mcp_medimageparse_segment_lesions` with `file_path` = the **absolute** path from step 1 and `prompts` = the assembled list. For each prompt the tool returns `detected`, `mask_path`, `pixel_count`, and `category`.

4. **Hand off to `write-report-simple`.** Invoke the `write-report-simple` skill (already in the workspace skill drawer at `.github/skills/write-report-simple/`). Pass:
   - `findings`: one entry per prompt — `present` when `detected` is true, `absent` when false (e.g. `enhancing tumor: present`, `non-enhancing tumor: absent`). Presence comes from the tool; use your own read of the image only for location wording.
   - No `measurements` — nothing has measured the lesion yet, so the report describes size qualitatively.

5. **Return what `write-report-simple` returns.** Do not re-wrap, re-format, or annotate the report. The downstream skill emits the `<confidence>` and `<report>` blocks; pass them through unchanged.

## Critical rules

- **Presence comes from the masks.** Do not report a lesion component whose prompt came back `detected: false`, and do not drop one that came back `detected: true`.
- **`pixel_count` is not a size.** Do not convert it into millimeters or an area.
- **The report must not mention MedImageParse, masks, prompts, or any model output.** That's the responsibility of `write-report-simple` (which has the rule baked in), but it's worth restating here: this skill exists to ground the report in vision-model evidence, not to surface that evidence in the prose. If you want to attribute or caveat the model in the chat reply *outside* the `<report>` tags, that's fine.
