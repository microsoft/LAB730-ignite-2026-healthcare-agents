---
name: write-report-simple
description: Write a structured chest X-ray report (Indication, Technique, Findings, Impression) using canonical radiologist phrasings. Invoke whenever drafting or revising a CXR report.
argument-hint: |
  - findings: optional list of findings the caller already identified (e.g. from another tool)
  - scores: optional classifier probabilities or confidence values per finding (e.g. from a zero-shot or adapter model in later steps)
  - confidence: optional explicit hint about how certain the caller is (low / medium / high)
---

# write-report-simple

Formats a CXR report (Indication, Technique, Findings, Impression) using canonical radiologist phrasing. Does not run image models or look up priors.

If the caller provides `findings`, `scores`, or `confidence`, use them to calibrate prose hedging and the emitted confidence value. Prefer explicit `confidence` > per-finding `scores` > tone of `findings`. When nothing is provided, derive everything from the image.

## Budget

- Tool calls: 0 — this skill writes the report; it does not call tools.
- Output: ≤ 200 words for the full report.
- Do not re-invoke skills already used in this turn.
- Do not retry tool calls on success.

## How to use

1. Use this section structure, in this order, with all-caps headers:

   ```
   INDICATION:
   TECHNIQUE:
   FINDINGS:
   IMPRESSION:
   ```

   - **INDICATION** — one short sentence on clinical context. If none was provided, write: `Not provided.`
   - **TECHNIQUE** — one sentence describing the study (view, technique). Default: `Frontal chest radiograph.`
   - **FINDINGS** — impersonal declarative sentences. Mention all standard structures (lungs, pleura, heart, mediastinum, bones, any devices) even when normal.
   - **IMPRESSION** — **numbered**, prioritized by clinical significance. One concise statement per number. Hedging language permitted.
   - Plain text only — no markdown. The all-caps section labels are the only headers.

2. Borrow phrasings from [`references/phrase-bank.md`](references/phrase-bank.md).
3. Apply the style rules below.
4. Wrap output in `<confidence>` and `<report>` tags as shown in **Output format**.

## Style rules

- **Findings** states observations; **Impression** states interpretations.
- Match hedge strength to evidence:
  - High evidence or high scores: state directly. `Right lower lobe pneumonia.`
  - Moderate: use `possible` or `differential includes`.
  - Low but non-zero: use `cannot exclude`.
  - Absent: omit, or state the negative if clinically relevant.
- State negatives explicitly. Group them: `No pleural effusion or pneumothorax.`
- No padding, filler, or clinical disclaimers.
- Present tense.

## Output format

```
<confidence>{confidence}</confidence>
<report>
{report}
</report>
```

- `{confidence}` — `low`, `medium`, or `high`. Use the caller-supplied value if given; otherwise derive from image evidence. Emit `low` when image quality limits the read, and note the limitation in Findings.
- `{report}` — plain text, no markdown. Four sections in order: INDICATION, TECHNIQUE, FINDINGS, IMPRESSION (see step 1 above).
