---
name: lookup-patient-history
description: Load the synthetic patient chart and verbatim prior reports for EHR reporting. Use before measuring the selected current and prior images; this lookup does not perform segmentation or measurements.
argument-hint: |
  - image_path: required path to the current image, named `{patient_id}_{study_index}.nii.gz`.
  - patient_id: optional override if the filename does not follow that convention.
---

# Lookup Patient History

Read `data/patients/{patient_id}.json` relative to the workspace root and inline its referenced prior reports. Return data, not a clinical interpretation.

## Scope and handoff

- File reads and file searches are permitted. Do not call segmentation or measurement tools **during this lookup step**. This restriction ends when the lookup returns; the parent report workflow must then perform its measurement steps.
- When used by a report skill, return the record internally and resume the parent workflow. Do not treat this helper's completion as the final chat response.
- When explicitly requested on its own, return only the patient-record block.
- Keep the block concise, but preserve all study dates, paths, treatment and procedure details, LAST RECORD ENTRY NOTE, and full prior report text. Do not truncate these to meet a word budget.

## How to use

1. **Resolve the identifiers.**
   - Use a supplied `patient_id`; otherwise infer it by removing `.nii.gz` and the trailing `_NNN` from the filename, for example `SYN0056_006.nii.gz` gives `SYN0056`.
   - Retain the current `study_id` to identify the matching pending order. If the filename does not identify the patient or study and the caller has not supplied it, request clarification rather than guessing.
2. **Read the chart.**
   - Read `data/patients/{patient_id}.json`.
   - If the file does not exist, return `PATIENT RECORD: Not on file for patient_id {patient_id}.` to the parent, which must still measure the current image. This ends only the lookup.
   - If the file exists but cannot be read or parsed, report the specific error and stop the workflow; do not mislabel it as a missing chart.
3. **Inline prior reports.**
   - For each non-null `report_path` in `imaging_studies`, read the report and include its full text verbatim.
   - Resolve paths from the workspace root. If a report is not there, look for the same filename in the neighboring reports directory; do not substitute a different study.
   - If a report remains missing, include `[report file missing: {path}]` and continue with the other chart data. The parent must disclose that missing source.
4. **Return the block below**, preserving the section headers. Mark the pending order that matches the current study.

## Output format

```text
PATIENT RECORD - {patient_id}, as of {record_as_of}

DEMOGRAPHICS: {demographics.age}{demographics.sex}.

DIAGNOSIS: {diagnosis.primary} {diagnosis.molecular} Established {diagnosis.established}

PRESENTATION: {presentation.date}. {presentation.presenting_complaint}
HPI: {presentation.hpi_summary}

ACTIVE PROBLEMS:
- {each item from active_problems}

PAST MEDICAL HISTORY:
- {each item from past_medical_history}

ALLERGIES: {allergies.notes}

CURRENT MEDICATIONS:
- {name} {dose} - {indication}
  (one line per item from medications)

PROCEDURES:
- {date}: {procedure}. {result} Complications: {complications}
  (one line per item from procedures)

TREATMENTS:
- {start} -> {end, or "ongoing" if null}: {treatment}. {notes}
  (one line per item from treatments)

EXPECTED POST-TREATMENT FINDINGS (per record):
- {each item from expected_post_treatment_findings}

IMAGING HISTORY (oldest to newest):
- {study_id} - {date}, {exam}. {summary} Image: {image_path, or "not retained"}
  (one line per imaging_studies entry)

PRIOR REPORTS:
=== {study_id} ({date}) ===
{full report text loaded from report_path, or the missing-file notice}
===
  (one block per imaging_studies entry with a report_path)

PENDING ORDERS:
- {study_id} - {date}, {exam}. Indication: {indication} Status: {status}
  (one line per pending_orders entry; mark the matching study with "<- current image")

LAST RECORD ENTRY NOTE: {last_record_entry_note}
```

## Critical rules

- Do not invent fields. Render missing, empty, or null fields as `(none)` unless the format specifies otherwise.
- Do not summarize the prior report or substitute its measurements for a current image measurement.
- Do not interpret findings or decide which lesion is new. The parent report skill combines the record with imaging evidence.
- Always include LAST RECORD ENTRY NOTE so the report writer knows where the record ends.
