---
name: write-report-with-ehr
description: Write a context-aware brain MRI follow-up report grounded in MedImageParse lesion segmentation, tool-computed lesion measurements, AND the patient's EHR record. Adds a COMPARISON section and uses the most recent prior report and the treatment timeline to call out interval change.
argument-hint: |
  - image_path: required path to the current brain MRI image (axial slice, PNG).
  - patient_id: optional override if the image filename does not follow the `{patient_id}_{study_index}.png` convention.
---

# write-report-with-ehr

Four steps: (1) `lookup-patient-history`, (2) one `mcp_medimageparse_segment_lesions` call on the current image, (3) one `mcp_medimageparse_measure_lesions` call on the primary target's mask, (4) write a comparison-aware report. Self-contained — does not delegate.

## Budget

- Tool calls: 2 (segment + measure, current image only — **do not re-segment the prior**).
- Skill invocations: 1 (`lookup-patient-history`).
- Output: ≤ 250 words. No retries on success.

## How to use

1. **Look up the EHR.** Invoke `lookup-patient-history` with the current `image_path`. If "Not on file," continue and write `COMPARISON: None available.`
2. **Segment the current image.** Resolve `image_path` to absolute (the MCP tools run in a different cwd). Pick the prompt set for the image's sequence (the `sequence` field in the sidecar JSON next to the image) from [`../write-report-segmentation/references/prompts.md`](../write-report-segmentation/references/prompts.md) and call `mcp_medimageparse_segment_lesions` once.
3. **Measure.** If the primary target (the first prompt in the set) was detected, call `mcp_medimageparse_measure_lesions` with its `mask_path`. It returns the patient `side` and `longest_diameter_mm` × `perpendicular_diameter_mm` per lesion, largest first.
4. **Write the report** using the format below, anchoring comparison to the most recent `PRIOR REPORTS` block from the lookup.

## Why comparison matters

When a prior exists, the clinician already knows what's there. Your job is **what changed, and what it means given the treatment timeline.**

- Surface real change — new, increased, decreased, resolved.
- De-escalate expected findings — the resection cavity and post-treatment changes listed under `EXPECTED POST-TREATMENT FINDINGS` are *expected*; describe them in one sentence, do not call them new.
- Read change against the treatment timeline. After brain radiation, an enhancing lesion can enlarge because of treatment effect (pseudoprogression) rather than tumor growth, most often within about 12 weeks of finishing chemoradiation. If the record places the current study inside that window (check `PENDING ORDERS` and `TREATMENTS`), say that treatment-related change and tumor progression cannot be distinguished — do not call progression outright.
- Anchor recommendations to trajectory — "increased within the post-radiation window" ≠ "increased six months after treatment" even when the imaging looks identical.

## Comparison rules

- **`COMPARISON:` line is required.** Cite exam, date, and `study_id` of the most recent prior report. If none, `None available.`
- **Quote both measurements verbatim** — the current one from `measure_lesions`, the prior one from the prior report: `now {current} mm, previously {prior} mm`. **Do not compute** percentages, products, or differences, and do not assign response categories (e.g. RANO) — that's the radiologist's call.
- **Use canonical change words**, one per finding: *stable, unchanged, increased, decreased, new, resolved, interval increase/decrease, no significant change.*
- **Walk Findings in roughly the prior's order.** State change (or stability) explicitly.
- **Stable findings get one sentence.** Save prose for what changed.
- **Don't invent priors.** If a current finding isn't in the prior report or EHR, write *new* — not *stable*.
- **Respect the record's last entry.** If `LAST RECORD ENTRY NOTE` says the record stops before the current study, do not assume what happened in the gap.
- **Impression is change-first** — interval change and its treatment context first, expected post-treatment findings last.

## Hedging and style

- Detected targets → state directly. Not detected → omit, or state the negative if clinically relevant.
- Laterality and sizes come from `measure_lesions` only. Never estimate either from the image.
- State negatives explicitly and grouped. Present tense, impersonal declaratives, plain text.
- The report **must not** mention MedImageParse, masks, prompts, tool calls, EHR JSON, or any model output.

## Output format

Return the two trace sections first, then the report block last.

```
## Prior information used

Bulleted summary of what `lookup-patient-history` returned that you actually
leaned on — diagnosis, treatments and their dates, expected post-treatment
findings, the prior study you anchored COMPARISON to, and any phrases or
measurements from the prior report you carried forward. If no prior was
available, say so. **Max 6 bullets, one line each.**

## Clinical details used in the report

Bulleted, one bullet per substantive phrase in the report. Each bullet pairs
the report phrase with the source that backed it — an EHR field (`diagnosis`,
`treatments`, `expected_post_treatment_findings`, `pending_orders`,
`prior report _NNN`) or a tool call (`segment: enhancing tumor detected`,
`measure: side and diameters`). Flag anything not supported by either
source. **Max 10 bullets, one line each.**

<confidence>{confidence}</confidence>
<report>
INDICATION: {one sentence from the pending order's indication for the current study}
TECHNIQUE: {one sentence (plane, sequence, contrast)}
COMPARISON: {exam, date, study_id of most recent prior — or "None available."}
FINDINGS: {impersonal declarative sentences in prose paragraphs. Each finding tagged with a canonical change word. Quote current and prior measurements verbatim. Describe expected post-treatment findings as expected.}
IMPRESSION: {change-first prose, one short paragraph or numbered "1. ... 2. ..." inline on one line — no markdown lists.}
</report>
```

**The `<report>` block is plain text only — no markdown.** No bullets, no `-`/`*` lists, no numbered-list line breaks, no bold/italic, no headers. Section labels (`INDICATION:` etc.) are the only structure.

`{confidence}` is `low` / `medium` / `high`, derived from how clearly the tools and the record support the findings, and from image quality.