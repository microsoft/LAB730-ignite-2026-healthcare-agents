---
name: write-report-simple
description: Write a concise brain MRI report (Exam, Indication, Comparison, Technique, Findings, Impression). Invoke whenever drafting or revising a brain MRI report.
argument-hint: |
  - findings: optional list of findings the caller already identified (e.g. lesions reported by a segmentation tool)
  - measurements: optional per-lesion tool measurements with units and patient laterality, copied as supplied, never estimated
  - confidence: optional explicit hint about how certain the caller is (low / medium / high)
---

# write-report-simple

Write the report without calling tools, measuring lesions, or looking up priors.

Use explicit `confidence` > tool-provided `findings` and `measurements` > your image read. Copy authoritative measurements, units, and patient laterality verbatim. Without supplied findings, interpret the images or series; without tool measurements, use qualitative sizes.

## Budget

- Tool calls: 0.
- Full report: at most 200 words.
- Do not re-invoke skills already used in this turn.

## How to use

Keep these six sections in order, separated by blank lines. Text follows the first four headers inline; FINDINGS is one prose paragraph; IMPRESSION is numbered, one statement per line.

```text
EXAM: MRI brain without and with contrast.

INDICATION: Not provided.

COMPARISON: None.

TECHNIQUE: Axial post-contrast T1-weighted MRI of the brain.

FINDINGS:
{One prose paragraph: lesion findings first, then a brief routine survey.}

IMPRESSION:
1. {Most important finding.}
2. {Next finding, if needed.}
```

- EXAM names the supplied examination, not an inferred protocol. INDICATION defaults to `Not provided.` COMPARISON defaults to `None.`; otherwise use the supplied prior date or description.
- TECHNIQUE names the available series, plane, and contrast status; if unknown: `MRI of the brain; sequence details not provided.` Only for a single series, add a matching FINDINGS limitation: `Evaluation is limited to a single post-contrast series.`
- FINDINGS: lesion location and patient laterality, enhancement, size, edema, then mass effect. Follow with ventricles and sulci, extra-axial spaces, midline, and other assessable findings, even when normal. State required areas that cannot be assessed.
- Prioritize IMPRESSION by clinical significance. Adapt [references/phrase-bank.md](references/phrase-bank.md), then apply the rules and wrapper below.

## Style rules

- FINDINGS states observations; IMPRESSION states interpretations. State supported findings directly, use `possible` for moderate uncertainty and `cannot exclude` for low but non-zero suspicion.
- Comparison terms (`again seen`, `redemonstrated`, change, `no new lesions`) require supplied prior evidence.
- State supported negatives briefly. Diffusion, white matter signal, blood products, and flow voids require appropriate sequences or supplied findings, not a post-contrast series alone.
- **Numbers come from tools only.** Copy sizes and midline shift verbatim from `measurements`, with units and dimensions as supplied (e.g. `{a} x {b} x {c} cm`). Never round, convert, add dimensions, or estimate numbers from images. Otherwise describe size or shift qualitatively.
- **Laterality is the patient's.** In radiological display, the patient's right is on image left. Prefer tool-supplied laterality.
- Use present tense, no filler or clinical disclaimers, and no mention of tools, models, masks, or scores inside the report.

## Output format

```text
<confidence>{confidence}</confidence>
<report>
{report}
</report>
```

- `{confidence}`: `low`, `medium`, or `high`. Prefer the caller's value; otherwise derive from evidence, using `low` for limited image quality. Note image-quality limitations in FINDINGS.
- `{report}`: the six-section plain-text layout above, without markdown or code fences. Impression numbering is literal text.