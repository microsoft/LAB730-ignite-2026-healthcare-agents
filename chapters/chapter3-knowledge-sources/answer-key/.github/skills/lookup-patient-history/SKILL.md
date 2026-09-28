---
name: lookup-patient-history
description: Load a synthetic patient EHR record (demographics, HPI, problems, meds, devices, prior imaging studies and reports) for a given chest X-ray. Invoke as the first step of any context-aware reporting flow that needs patient history. No model calls.
argument-hint: |
  - image_path: required path to the current CXR image. The patient_id is inferred from the filename (NIH convention `{patient_id}_{idx}.png`).
  - patient_id: optional override if the image filename does not follow NIH convention.
---

# lookup-patient-history

Pure data skill. Reads the on-disk patient record at `/data/patients/{patient_id}.json` and returns it, with any referenced prior reports loaded inline. No model calls, no scoring, no prose.

This skill is the "knowledge source" half of chapter 4 — the report-writing skill consumes whatever this returns.

## Budget

- Tool calls: 0 (only file reads).
- Output: structured block, ≤ 400 words.
- Do not re-invoke skills already used in this turn.

## How to use

1. **Resolve `patient_id`.**
   - If the caller supplied `patient_id`, use it.
   - Otherwise infer from the image filename: NIH convention is `{patient_id}_{study_index}.png` (e.g. `00026132_011.png` → `00026132`). Strip the trailing `_NNN.png`.

2. **Load the record file.**
   - Path: `/data/patients/{patient_id}.json` (workspace-root-relative).
   - If the file does not exist, return:
     ```
     PATIENT RECORD: Not on file for patient_id {patient_id}.
     ```
     and stop.

3. **Inline any prior reports.**
   - For each entry in `imaging_studies` that has a non-null `report_path`, read the file at that path and include the full report text in the returned block. Analyze report path and look for report in the neighboring reports directories if not found at the specified path.
   - If the file is missing, note `[report file missing: {path}]` instead of the report text and continue. Do not stop or fail the whole skill if a prior report file is missing — just note it and move on.

4. **Return the block.** Use the format below verbatim — the report-writing skill expects these section headers.

## Output format

```
PATIENT RECORD — {patient_id}, as of {record_as_of}

DEMOGRAPHICS: {age}{sex}.

ADMISSION: {admission.admit_date}, hospital day {admission.hospital_day_as_of_record}, {admission.service}.
Presenting complaint: {admission.presenting_complaint}
HPI: {admission.hpi_summary}

ACTIVE PROBLEMS:
- {each item from active_problems}

PAST MEDICAL HISTORY:
- {each item from past_medical_history}

ALLERGIES: {allergies.notes}

CURRENT MEDICATIONS:
- {name} {dose} — {indication}
  (one line per item from medications)

PROCEDURES:
- {date} (HD{hospital_day}): {procedure}. {result} Complications: {complications}.
  (one line per item from procedures)

INDWELLING DEVICES (per record):
- {each item from indwelling_devices_as_of_record}

IMAGING HISTORY (oldest → newest):
- {study_id} — {date} (HD{hospital_day}), {modality} {view}. {summary}
  (one line per imaging_studies entry; preserve order)

PRIOR REPORTS:
=== {study_id} ({date}, HD{hospital_day}) ===
{full report text loaded from report_path}
===
  (one block per imaging_studies entry that has a report_path; in order)

LAST RECORD ENTRY NOTE: {last_record_entry_note}
```

## Critical rules

- **Do not invent fields.** If a field is empty, missing, or null, render it as `(none)` or omit the line. Never fabricate.
- **Do not summarize the prior report.** Inline the full text verbatim. The report writer needs the original phrasing for comparison.
- **Do not interpret findings.** This skill returns data, not analysis.
- **The record may not be current.** Always include `LAST RECORD ENTRY NOTE` so the report writer knows where the record ends.
