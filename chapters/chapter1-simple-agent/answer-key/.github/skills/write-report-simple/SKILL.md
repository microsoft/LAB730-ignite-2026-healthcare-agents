---
name: write-report-simple
description: Write a structured brain MRI report (Indication, Technique, Findings, Impression) using canonical neuroradiology phrasings. Invoke whenever drafting or revising a brain MRI report.
argument-hint: |
  - findings: optional list of findings the caller already identified (e.g. lesions reported by a segmentation tool)
  - measurements: optional per-lesion measurements from a measurement tool (e.g. longest and perpendicular diameters in mm, laterality) — reported verbatim, never estimated
  - confidence: optional explicit hint about how certain the caller is (low / medium / high)
---

# write-report-simple

Formats a brain MRI report (Indication, Technique, Findings, Impression) using canonical neuroradiology phrasing. Does not run image models, measure lesions, or look up priors.

If the caller provides `findings`, `measurements`, or `confidence`, use them to ground the prose and the emitted confidence value. Prefer explicit `confidence` > tool-provided `findings` and `measurements` > your own read of the image. `measurements` are authoritative — copy the numbers and laterality verbatim. When nothing is provided, derive findings from the image and describe lesion size qualitatively; never invent numeric measurements.

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
   - **TECHNIQUE** — one sentence describing the image (plane, sequence, contrast). Default: `Axial MRI image of the brain.` Name the sequence when known, e.g. `Axial post-contrast T1-weighted image of the brain.`
   - **FINDINGS** — impersonal declarative sentences. Cover any lesion (location, laterality, size, signal or enhancement), surrounding edema, mass effect and midline, ventricles, and extra-axial spaces even when normal. With a single image, state once: `Evaluation is limited to the provided axial image.`
   - **IMPRESSION** — **numbered**, prioritized by clinical significance. One concise statement per number. Hedging language permitted.
   - Plain text only — no markdown. The all-caps section labels are the only headers.

2. Borrow phrasings from [`references/phrase-bank.md`](references/phrase-bank.md).
3. Apply the style rules below.
4. Wrap output in `<confidence>` and `<report>` tags as shown in **Output format**.

## Style rules

- **Findings** states observations; **Impression** states interpretations.
- Match hedge strength to evidence:
  - Tool-confirmed or unequivocal: state directly. `Enhancing mass in the left frontal lobe.`
  - Moderate: use `possible` or `differential includes`.
  - Low but non-zero: use `cannot exclude`.
  - Absent: omit, or state the negative if clinically relevant.
- State negatives explicitly. Group them: `No hemorrhage, hydrocephalus, or midline shift.`
- **Numbers come from tools only.** Give sizes in millimeters only when supplied in `measurements`, copied verbatim (`measures {longest} × {perpendicular} mm (longest × perpendicular, axial)`). Otherwise describe size qualitatively (`small`, `moderate`, `large`). Never estimate millimeters from the image.
- **Laterality is the patient's.** Images use radiological convention (patient's right on image left). Prefer tool-supplied laterality when given.
- Never mention tools, models, masks, or scores inside the report.
- No padding, filler, or clinical disclaimers.
- Present tense.

## Output format

```
<confidence>{confidence}</confidence>
<report>
{report}
</report>
```

- `{confidence}` — `low`, `medium`, or `high`. Use the caller-supplied value if given; otherwise derive from the evidence. Emit `low` when image quality limits the read, and note the limitation in Findings.
- `{report}` — plain text, no markdown. Four sections in order: INDICATION, TECHNIQUE, FINDINGS, IMPRESSION (see step 1 above).