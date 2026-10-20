---
name: write-report-with-ehr
description: Write a context-aware brain MRI report using the patient chart and mandatory tool-computed linear and volumetric measurements. Use for EHR reporting with Radiology Assistant (EHR).
argument-hint: |
  - image_path: required path to the current brain MRI image, named `{patient_id}_{study_index}.nii.gz`.
  - patient_id: optional override if the filename does not follow that convention.
---

# Write Report with EHR

Combine the patient record with measured imaging evidence. Write the report here; do not delegate to another report skill.

## Required before writing a report

Do not emit `<report>` until all of these conditions are satisfied for this request:

1. `list_models` has returned the model catalog and its ordered tumor-component prompts.
2. `segment` and `clean_segmentation` have succeeded for the current image and the selected prior image, if any.
3. `describe_lesions` has succeeded with the current `clean_path` and, when a prior was selected, its `prior_clean_path`.
4. The factsheet and final FINDINGS include every applicable measurement in the checklist below.

The factsheet helper performs the tool calls. Loading a skill or finding an old factsheet does not satisfy these conditions. Do not substitute a prior report, visual estimates, raw segmentation volumes, or a simpler report skill.

If a required tool is unavailable or fails, stop without `<report>`. Identify the failed step and image, report the error, and tell the user what to check, such as the `medimageparse` server in the tool picker. A missing chart is not a measurement failure: measure the current scan even when history is unavailable.

## How to use

1. **Look up the record.** Follow [lookup-patient-history](../lookup-patient-history/SKILL.md) with `image_path` and any `patient_id` override. Its restrictions apply only during lookup. After it returns the record or "Not on file," continue this workflow.
2. **Pick the prior image.** Use the most recent study in IMAGING HISTORY before the current exam that has a retained image. Use the current study's matching pending order to establish its date. Resolve both image paths to absolute paths. If a selected image cannot be read, stop and identify the path; do not silently drop the prior. With summary-only priors, measure only the current scan and compare with the summaries in words. If the current study cannot be identified in the chart, request clarification instead of guessing its order or prior.
3. **Measure.** Follow [write-imaging-factsheet-ehr](../write-imaging-factsheet-ehr/SKILL.md) with the current image and selected prior, or the current image alone. Keep the factsheet, its path, `descriptors_path`, and each scan's `audit_dir`. Resume this report workflow after the helper finishes; do not end the response with the factsheet.
4. **Check the evidence.** Check the factsheet against the returned descriptors and the checklist below. If a factsheet field was omitted, copy it from the same descriptor result or its saved JSON. If a required source field is missing, stop and name it; do not invent it. Do not rerun successful segmentation to repair transcription.
5. **Draft and check.** Write the two trace sections and the report. Check the actual FINDINGS against each checklist row before returning. Measurements appearing only in the factsheet or trace do not satisfy the report requirement.

If the chart is "Not on file," skip prior selection, use `EXAM: MRI brain.`, `INDICATION: Not provided.`, and `COMPARISON: None available.`, and flag the missing history in the trace. Do not invent an order, date, treatment, or location.

## Required measurement checklist

Copy the displayed values and units from the factsheet, without computing, rounding, converting, or using `unrounded_*` fields.

| Include in FINDINGS | Descriptor source |
|---|---|
| Current lesion count | `total.lesion.count`: `value`, `unit` |
| Both diameters for **each current lesion**, in cm | `L*.bidimensional`: `diameters_cm[0]` and `diameters_cm[1]` |
| AP x TR extents for **each current lesion**, with their unit | `L*.extent`: `value.AP`, `value.TR`, `unit` |
| Enhancing, necrotic, and tumor-core volumes for **each current lesion** | `L*.volume.enhancing`, `L*.volume.necrotic`, `L*.volume.tumor_core`: `value`, `unit` |
| Total enhancing, necrotic, tumor-core, edema, and whole-tumor volumes | Corresponding `total.volume.*`: `value`, `unit` |
| Total sum of diameter products | `total.sum_of_products`: `value`, `unit` |
| With a measured prior, every returned change line, including its named quantity | Each `change.*`: `prior`, `current`, `unit`, `percent_change`, `percent_change_unit`, and any `reason` |

`L*` means every current lesion ID, not just `L1`. In a bidimensional descriptor, **`value` is the product in cm2, not a diameter**. The AP/TR extents are bounding-box dimensions, not the two bidimensional diameters; label them separately.

Use this sentence shape for each current lesion, adding location only when supported:

```text
Lesion {number} measures {diameters_cm[0]} x {diameters_cm[1]} cm; AP x TR extent is {AP} x {TR} cm. Enhancing, necrotic, and tumor-core volumes are {enhancing} mL, {necrotic} mL, and {tumor_core} mL, respectively.
```

- `measurable: false` does not mean the diameters are missing. Include both returned diameters even when the lesion is below the measurement threshold.
- An explicit `null` with a reason is an unavailable value: preserve both in the factsheet and state the unavailability and reason in the report. Do not turn it into zero or silently omit it. A missing field is not an explicit null.
- When `total.lesion.count` is zero, state that no lesions were identified and include the returned totals and any change lines. Omit per-lesion sentences; never invent a lesion or dimensions.
- Without a retained prior image, there are no tool-computed change lines. Do not calculate change from historical report measurements.
- Keep the report near 250 words where practical. **Required measurement coverage and limitations take precedence over the word target.**

## Reading the change and using sources

- Check PROCEDURES and TREATMENTS between the measured prior and current exam. If the comparison crosses a resection, say so; do not call it growth of the same lesion. Compare with later summary-only studies, such as the post-operative baseline, in words.
- After radiation, enhancement and edema can increase without tumor growth. When the record supports both treatment effect and tumor, state that imaging alone cannot separate them rather than calling progression.
- Answer the current pending order in IMPRESSION. Mention steroids when discussing edema or mass effect, and describe expected post-treatment findings without calling them new.
- Lesion IDs are scan-local ranks, not cross-exam matches. Change descriptors compare totals. Never match current and prior lesions by ID.
- Historical report measurements, including CT midline shift, must retain their source study and date; they are not current MRI measurements.
- Location and side come from the record or a supported image read, never descriptor IDs. Do not infer unsupported anatomy or negatives from a single sequence.
- Preserve applicable factsheet limitations, including T1-only edema assessment and geometric measurement proxies. Do not present `measurable` as clinical response eligibility.
- Do not invent priors or events after LAST RECORD ENTRY NOTE. Keep tools, models, masks, descriptor IDs, and JSON out of the report; cite them only in the trace.

## Output format

Return the two trace sections first, then the confidence and report blocks last. Keep trace bullets concise, but do not omit required source mappings to meet a bullet limit.

```text
## Prior information used

- Record fields and prior studies relied on, including the measured prior and any intervening procedure.
- Factsheet path and each scan's audit-log folder, current first.
- Missing history or unavailable prior reports, if any.

## Clinical details used in the report

- Each substantive report phrase paired with its record field, dated prior report or study summary, or factsheet descriptor IDs.
- For each current lesion, explicitly cite its bidimensional, extent, and volume IDs. Include total and change IDs used. Flag anything without a source.

<confidence>{confidence}</confidence>
<report>
EXAM: {exam from the current pending order, or the missing-chart default}

INDICATION: {indication from the current pending order, or "Not provided."}

COMPARISON: {measured prior exam, date, and study_id; other relevant studies by date and study_id; or "None available."}

TECHNIQUE: {series, plane, and contrast; or "MRI of the brain; sequence details not provided."}

FINDINGS:
{Lesion count and one measurement sentence per current lesion, using the required sentence shape.}
{Named total volumes, sum of products, and each applicable change line, interpreted against intervening treatment.}
{Edema, mass effect, expected post-treatment findings, and applicable limitations with historical sources distinguished.}

IMPRESSION:
1. {Answer to the order, with the change in context; if there is no order, summarize supported findings.}
2. {Next finding, if needed.}
</report>
```

`confidence` is `low`, `medium`, or `high`, based on the evidence. Inside `<report>`, use plain text without markdown, bullets, or bold; impression numbering is literal text. Do not append the factsheet or audit folders after the report.
