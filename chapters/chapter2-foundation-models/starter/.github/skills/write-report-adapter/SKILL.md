---
name: write-report-adapter
description: Write a chest X-ray report grounded in the trained MedImageInsight (MI2) adapter. Invoke whenever drafting a CXR report when the adapter is available — get vision-grounded per-finding positive/possible/negative calls, then delegate the prose to `write-report-simple`.
argument-hint: |
  - image_path: required path to the CXR image (PNG or JPEG)
  - head: optional adapter head — "mlp" (default) or "svm"
---

# write-report-adapter

Two-step skill: (1) call the trained MI2 adapter to get per-finding positive/possible/negative calls for the image, then (2) hand those off to the existing `write-report-simple` skill to produce the actual report. The report itself never mentions MI2, the adapter, or any classifier — it reads as the radiologist's direct read of the image.

## Budget

- Tool calls: 1 — exactly one `mcp_medimageinsig_adapter_classify` call per image.
- Output: ≤ 200 words for the full report.
- Do not re-invoke skills already used in this turn.
- Do not retry tool calls on success.

## How to use

1. **Resolve the image to an absolute path.** The MCP tool runs in a different working directory than the agent. If `image_path` is not absolute, resolve it (e.g. via `realpath`) before calling the tool. If you can't resolve it, ask the user.

2. **Get calls from the adapter.**
   - Call `mcp_medimageinsig_adapter_classify` with `file_path` = the **absolute** path from step 1, and `head` = the caller's `head` if provided (otherwise omit; defaults to `mlp`).
   - The adapter returns `{label: "positive" | "possible" | "negative"}` — already bucketed using per-class operating points fit during training (Youden-J for rule-in, sens90 for rule-out). No further thresholding.

3. **Hand off to `write-report-simple`.** Invoke the `write-report-simple` skill (already in the workspace skill drawer at `.github/skills/write-report-simple/`). Pass:
   - `findings`: the list of labels with call `"positive"` or `"possible"`, using the original adapter label names. Omit negatives.

   The downstream skill derives confidence from the positive/possible mix. The adapter's `possible` label maps to hedged language (`possible`, `differential includes`, `cannot exclude`) in the report.

4. **Return what `write-report-simple` returns.** Do not re-wrap, re-format, or annotate the report. The downstream skill emits the `<confidence>` and `<report>` blocks; pass them through unchanged.

## Critical rule

**The report must not mention MI2, the adapter, classifier scores, or any model output.** That's the responsibility of `write-report-simple` (which has the rule baked in), but it's worth restating here: this skill exists to ground the report in vision-model evidence, not to surface that evidence in the prose. If you want to attribute or caveat the model in the chat reply *outside* the `<report>` tags, that's fine.
