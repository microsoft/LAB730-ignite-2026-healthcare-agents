---
name: write-report-with-ehr
description: Write a context-aware chest X-ray report grounded in the trained MedImageInsight (MI2) adapter AND the patient's EHR record. Adds a COMPARISON section and uses the most recent prior report to call out interval change.
argument-hint: |
  - image_path: required path to the current CXR image (PNG or JPEG).
  - head: optional adapter head — "mlp" (default) or "svm".
  - patient_id: optional override if the image filename does not follow NIH convention.
---

# write-report-with-ehr

Three steps: (1) `lookup-patient-history`, (2) one `mcp_medimageinsig_adapter_classify` call on the current image, (3) write a comparison-aware report. Self-contained — does not delegate.

## Budget

- Tool calls: 1 (adapter, current image only — **do not re-score the prior**).
- Skill invocations: 1 (`lookup-patient-history`).
- Output: ≤ 250 words. No retries on success.

## How to use

1. **Look up the EHR.** Invoke `lookup-patient-history` with the current `image_path`. If "Not on file," continue and write `COMPARISON: None available.`
2. **Score the current image.** Resolve `image_path` to absolute (the MCP tool runs in a different cwd). Call `mcp_medimageinsig_adapter_classify`. Each finding returns `positive` / `possible` / `negative` — already operating-point-bucketed.
3. **Write the report** using the format below, anchoring comparison to the most recent `PRIOR REPORTS` block from the lookup.

## Why comparison matters

When a prior exists, the clinician already knows what's chronic. Your job is **what changed and what to do about it.**

- Surface real change — new, worsening, resolved.
- De-escalate chronic findings — one stable sentence, not a paragraph.
- Don't alarm on documented hardware — lines/tubes in `INDWELLING DEVICES` are *expected*; confirm position, do not call them new.
- Anchor recommendations to trajectory — "worsening despite drainage" ≠ "stable post-drainage" even when the imaging looks identical.

## Comparison rules

- **`COMPARISON:` line is required.** Cite modality, view, date, and `study_id` of the most recent prior report. If none, `None available.`
- **Use canonical change words**, one per finding: *stable, unchanged, improved, worsened, progressed, new, resolved, interval increase/decrease, no significant change.*
- **Walk Findings in roughly the prior's order.** State change (or stability) explicitly.
- **Stable findings get one sentence.** Save prose for what changed.
- **Don't invent priors.** If a current finding isn't in the prior report or EHR, write *new* — not *stable*.
- **Respect the record's last entry.** If `LAST RECORD ENTRY NOTE` says the record stops before the current study, do not assume what happened in the gap.
- **Impression is change-first** — interval change first, chronicity last.

## Hedging and style

- `positive` → state directly. `possible` → *possible* / *differential includes*. `negative` → omit, or state if clinically relevant.
- State negatives explicitly and grouped. Present tense, impersonal declaratives, plain text.
- The report **must not** mention MI2, the adapter, classifier scores, EHR JSON, or any model output.

## Output format

Return the two trace sections first, then the report block last.

```
## Prior information used

Bulleted summary of what `lookup-patient-history` returned that you actually
leaned on — HPI, active problems, indwelling devices, the prior study you
anchored COMPARISON to, and any phrases from the prior report you carried
forward. If no prior was available, say so. **Max 6 bullets, one line each.**

## Clinical details used in the report

Bulleted, one bullet per substantive phrase in the report. Each bullet pairs
the report phrase with the source that backed it — an EHR field (`HPI`,
`active_problems`, `indwelling_devices`, `procedures`, `prior report _NNN`)
or an adapter call (`adapter: positive emphysema`). Flag anything not
supported by either source. **Max 10 bullets, one line each.**

<confidence>{confidence}</confidence>
<report>
INDICATION: {one sentence using the admission HPI / current clinical question}
TECHNIQUE: {one sentence (view, technique)}
COMPARISON: {modality view, date, study_id of most recent prior — or "None available."}
FINDINGS: {impersonal declarative sentences in prose paragraphs. Each finding tagged with a canonical change word. Confirm positions of documented indwelling devices.}
IMPRESSION: {change-first prose, one short paragraph or numbered "1. ... 2. ..." inline on one line — no markdown lists.}
</report>
```

**The `<report>` block is plain text only — no markdown.** No bullets, no `-`/`*` lists, no numbered-list line breaks, no bold/italic, no headers. Section labels (`INDICATION:` etc.) are the only structure.

`{confidence}` is `low` / `medium` / `high`, derived from the adapter mix and image quality.
