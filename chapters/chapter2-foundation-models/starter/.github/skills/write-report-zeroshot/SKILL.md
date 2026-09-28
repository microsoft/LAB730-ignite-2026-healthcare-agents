---
name: write-report-zeroshot
description: Write a chest X-ray report grounded in MedImageInsight (MI2) zero-shot classifier scores. Invoke whenever drafting a CXR report when MI2 is available — get vision-grounded per-finding probabilities, then delegate the prose to `write-report-simple`.
argument-hint: |
  - image_path: required path to the CXR image (PNG or JPEG)
  - extra_labels: optional list of additional MI2-format label strings to score alongside the default set
---

# write-report-zeroshot

Two-step skill: (1) call MI2 to get per-finding probabilities for the image, then (2) hand those off to the existing `write-report-simple` skill to produce the actual report. The report itself never mentions MI2 — it reads as the radiologist's direct read of the image.

## Budget

- Tool calls: 1 — exactly one `mcp_medimageinsig_zeroshot_classify` call per image.
- Output: ≤ 200 words for the full report.
- Do not re-invoke skills already used in this turn.
- Do not retry tool calls on success.

## How to use

1. **Resolve the image to an absolute path.** The MCP tool runs in a different working directory than the agent. If `image_path` is not absolute, resolve it (e.g. via `realpath`) before calling the tool. If you can't resolve it, ask the user.

2. **Get scores from MI2.**
   - Read the canonical label list from [`references/labels.md`](references/labels.md) and use those strings **verbatim**.
   - If the caller provided `extra_labels`, append them.
   - Call `mcp_medimageinsig_zeroshot_classify` with `file_path` = the **absolute** path from step 1 and `labels` = the assembled list.
   - Bucket the returned scores using the cutoffs below.

3. **Hand off to `write-report-simple`.** Invoke the `write-report-simple` skill (already in the workspace skill drawer at `.github/skills/write-report-simple/`). Pass:
   - `findings`: the bucketed list (positives + possibles), using the original MI2 label names.
   - `scores`: the raw per-finding probabilities (so the report skill can calibrate hedging).

   The downstream skill derives confidence from `scores`.

4. **Return what `write-report-simple` returns.** Do not re-wrap, re-format, or annotate the report. The downstream skill emits the `<confidence>` and `<report>` blocks; pass them through unchanged.

## Score buckets

Probabilities sum to ~1.0 across the label set. With the default label list, use these cutoffs:

- **≥ 0.20** → positive finding (pass to `write-report-simple` as a confident finding).
- **0.08 – 0.20** → possible finding (pass through; the report skill hedges accordingly).
- **< 0.08** → absent (omit from `findings`).

## Critical rule

**The report must not mention MI2, zero-shot scores, or any model output.** That's the responsibility of `write-report-simple` (which has the rule baked in), but it's worth restating here: this skill exists to ground the report in vision-model evidence, not to surface that evidence in the prose. If you want to attribute or caveat the model in the chat reply *outside* the `<report>` tags, that's fine.
