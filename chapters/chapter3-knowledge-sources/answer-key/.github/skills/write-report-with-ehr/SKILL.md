---
name: write-report-with-ehr
description: Write a context-aware brain MRI follow-up report from the patient's record, tool-computed lesion measurements, and change from the most recent prior image. Use when asked for a report that uses the patient's history, chart, or EHR.
argument-hint: |
  - image_path: required path to the current brain MRI image. The patient_id comes from the filename (`{patient_id}_{study_index}.nii.gz`).
  - patient_id: optional override if the filename does not follow that convention.
---

# write-report-with-ehr

Combine the patient record with descriptor measurements, then write a comparison-aware report. This skill writes the report itself; it does not delegate to `write-report-simple`.

## How to use

1. **Look up the record.** Invoke `lookup-patient-history` with `image_path`. If it returns "Not on file," continue without history and write `COMPARISON: None available.`
2. **Pick the prior image.** Use the most recent study in IMAGING HISTORY, before the current study, that has a retained image. Resolve the current and prior image paths to absolute paths.
3. **Measure.** Invoke `write-imaging-factsheet` with the current image and that prior image, or the current image alone if no prior image is retained. Keep its factsheet and each scan's `audit_dir`.
4. **Write the report** in the format below.

## Reading the change

- **Check what happened between the prior image and the current exam.** If PROCEDURES or TREATMENTS fall between them, such as a resection, the factsheet's change lines compare across that event. Say so, and do not describe the change as growth of the same lesion. Compare with later summary-only studies, such as a post-operative baseline, in words.
- **Read change against the treatment timeline.** After radiation, enhancement and edema can increase without tumor growth (pseudoprogression or radiation necrosis). When the record allows both treatment effect and tumor, say that imaging alone cannot separate them; do not call progression outright.
- **Expected findings are expected.** Describe items from EXPECTED POST-TREATMENT FINDINGS in one sentence; do not call them new.
- **Answer the order.** The IMPRESSION addresses the question in the current study's pending order.
- **Medications matter.** Mention steroids when describing edema or mass effect.

## Sources

- Measurements and change come from the factsheet only, copied verbatim with units. Do not compute, round, or convert numbers. Report on all available measurements, both volumetric and linear.
- Values from summary-only studies, such as midline shift on a CT, are quoted with that study's date; the tools did not measure them.
- Location and side come from the record or your own read of the image; the descriptors assign none.
- Do not invent priors. A finding absent from every prior report and summary is new.
- If LAST RECORD ENTRY NOTE says the record stops before the current exam, do not assume what happened in the gap.
- The report must not mention tools, models, masks, descriptors, or the record's JSON.

## Output format

Return the two trace sections first, then the report block last.

```
## Prior information used

Up to 6 one-line bullets: the record fields and prior studies you relied on, including the prior image you measured against and any procedure between it and the current exam.

## Clinical details used in the report

Up to 10 one-line bullets, one per substantive report phrase, each paired with its source: a record field (`diagnosis`, `procedures`, `medications`, `pending_orders`, `prior report _NNN`, `study _NNN summary`) or a factsheet descriptor ID (`[L1.bidimensional]`). Flag anything with no source.

<confidence>{confidence}</confidence>
<report>
EXAM: {exam from the current pending order}

INDICATION: {indication from the current pending order}

COMPARISON: {the prior image's exam, date, and study_id; then other relevant studies by date and study_id}

TECHNIQUE: {series, plane, and contrast; or "MRI of the brain; sequence details not provided."}

FINDINGS:
{One or two prose paragraphs: the lesion and its change first, with what happened in between; then edema and mass effect; then expected post-treatment findings in one sentence.}

IMPRESSION:
1. {Answer to the order, with the change in context.}
2. {Next finding, if needed.}
</report>
```

- `{confidence}`: `low`, `medium`, or `high`, from how clearly the factsheet and the record support the findings.
- The report is plain text, at most 250 words: no markdown, bullets, or bold. Impression numbering is literal text.
