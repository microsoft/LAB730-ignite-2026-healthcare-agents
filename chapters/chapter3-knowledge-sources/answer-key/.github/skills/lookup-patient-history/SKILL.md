---
name: lookup-patient-history
description: Load a synthetic patient EHR record (demographics, diagnosis, treatments, medications, expected post-treatment findings, prior imaging studies and reports, pending orders) for a given brain MRI image. Invoke as the first step of any context-aware reporting flow that needs patient history. No model calls.
argument-hint: |
  - image_path: required path to the current brain MRI image. The patient_id is inferred from the filename (convention `{patient_id}_{study_index}.png`).
  - patient_id: optional override if the image filename does not follow that convention.
---

# lookup-patient-history

Pure data skill. Reads the on-disk patient record at `/data/patients/{patient_id}.json` and returns it, with any referenced prior reports loaded inline. No model calls, no segmentation, no prose.

This skill is the "knowledge source" half of Chapter 3 — the report-writing skill consumes whatever this returns.

## Budget

- Tool calls: 0 (only file reads).
- Output: structured block, ≤ 450 words.
- Do not re-invoke skills already used in this turn.

## How to use

1. **Resolve `patient_id`.**
   - If the caller supplied `patient_id`, use it.
   - Otherwise infer from the image filename: the convention is `{patient_id}_{study_index}.png` (e.g. `SYN0417_003.png` → `SYN0417`). Strip the trailing `_NNN.png`.
   - Note the current `study_id` too (e.g. `SYN0417_003`) — it identifies which pending order the current image belongs to.

2. **Load the record file.**
   - Path: `/data/patients/{patient_id}.json` (workspace-root-relative).
   - If the file does not exist, return:
     ```
     PATIENT RECORD: Not on file for patient_id {patient_id}.
     ```
     and stop.

3. **Inline any prior reports.**
   - For each entry in `imaging_studies` that has a non-null `report_path`, read the file at that path and include the full report text in the returned block. Analyze the report path and look for the report in neighboring reports directories if it is not found at the specified path.
   - If the file is missing, note `[report file missing: {path}]` instead of the report text and continue. Do not stop or fail the whole skill if a prior report file is missing — just note it and move on.

4. **Return the block.** Use the format below verbatim — the report-writing skill expects these section headers.

## Output format

```
PATIENT RECORD — {patient_id}, as of {record_as_of}

DEMOGRAPHICS: {age}{sex}.

DIAGNOSIS: {diagnosis.primary} {diagnosis.molecular} Established {diagnosis.established}

PRESENTATION: {presentation.date}. {presentation.presenting_complaint}
HPI: {presentation.hpi_summary}

ACTIVE PROBLEMS:
- {each item from active_problems}

PAST MEDICAL HISTORY:
- {each item from past_medical_history}

ALLERGIES: {allergies.notes}

CURRENT MEDICATIONS:
- {name} {dose} — {indication}
  (one line per item from medications)

PROCEDURES:
- {date}: {procedure}. {result} Complications: {complications}
  (one line per item from procedures)

TREATMENTS:
- {start} → {end, or "ongoing" if null}: {treatment}. {notes}
  (one line per item from treatments)

EXPECTED POST-TREATMENT FINDINGS (per record):
- {each item from expected_post_treatment_findings}

IMAGING HISTORY (oldest → newest):
- {study_id} — {date}, {exam}. {summary}
  (one line per imaging_studies entry; preserve order)

PRIOR REPORTS:
=== {study_id} ({date}) ===
{full report text loaded from report_path}
===
  (one block per imaging_studies entry that has a report_path; in order)

PENDING ORDERS:
- {study_id} — {date}, {exam}. Indication: {indication} Status: {status}
  (one line per pending_orders entry; mark the one matching the current study_id with "← current image")

LAST RECORD ENTRY NOTE: {last_record_entry_note}
```

## Critical rules

- **Do not invent fields.** If a field is empty, missing, or null, render it as `(none)` or omit the line. Never fabricate.
- **Do not summarize the prior report.** Inline the full text verbatim. The report writer needs the original phrasing and measurements for comparison.
- **Do not interpret findings.** This skill returns data, not analysis.
- **The record may not be current.** Always include `LAST RECORD ENTRY NOTE` so the report writer knows where the record ends.