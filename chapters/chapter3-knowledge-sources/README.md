# Chapter 3 — Connect a knowledge source to the agent

**Time budget: ~10 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Chapter 2 complete, with all four `medimageparse` tools working and the `write-imaging-factsheet` skill under `.github/skills/`.

## Overview

In Chapter 2 the agent measured the 2018 scan against the 2017 scan and reported that the tumor core more than doubled. The number is correct, and it is misleading: the lesion was resected between those two exams. A radiologist reporting on such an exam would need to know additional **patient context**: the diagnosis, the treatments and their dates, the surgery, and what the order asks. In this chapter you give the agent a synthetic patient record and a comparison-aware report skill, run the same scans through it, and compare the reports.

There's nothing to write in this chapter. Copy in two skills and a small data folder, run the agent, and observe. Same scans, same tools, a different report once the agent can read the chart.

**Steps:**
1. Skim the patient record. (~3 min)
2. Copy the two skills and the `data/` folder into your workspace. (~2 min)
3. Run the agent on the current study. (~3 min)
4. Compare with your Chapter 2 report. (~2 min)

> The patient records under `data/patients/` are **synthetic**, built around de-identified MRI reports.

## Step 1 — Skim the patient record (~3 min)

Open [data/patients/SYN0056.json](data/patients/SYN0056.json). The shape is intentionally simple (not something that a real-world export from an EHR would look like): flat fields, easy to read. Patient `SYN0056` is the case you measured in Chapter 2.

Things to notice:

- **`diagnosis`**: lung adenocarcinoma with a solitary right parietal brain metastasis.
- **`treatments`**: CyberKnife radiosurgery to the metastasis in October 2016, then maintenance chemotherapy.
- **`procedures`**: right parietal craniotomy and resection on **2017-08-17**. Pathology was mostly radiation necrosis with a small focus of viable tumor.
- **`imaging_studies`**: `_000` to `_005`. Only `_002` (2017-06-13) has a retained image and a full report. `_003` is the post-operative MRI summary: thin smooth enhancement, no nodular enhancement. `_004` and `_005` are head CTs with a 6 mm midline shift.
- **`medications`**: dexamethasone since 2018-04-09, for the edema.
- **`pending_orders`**: the current MRI, `_006` (2018-04-14): *assess for recurrent tumor versus radiation necrosis.*
- **`last_record_entry_note`**: the chart stops at the `_006` order.

Then open [data/reports/SYN0056_002.md](data/reports/SYN0056_002.md), the prior report, which measured the mass at 4.3 × 3.4 × 4.3 cm.

>**Why the history matters**. A larger mass on a follow-up scan does not necessarily mean that a tumor has continued to grow. Here, the earlier scan was taken before the lesion was surgically removed. The patient also received radiation treatment, and the removed tissue contained both radiation-related damage and viable tumor. Knowing this, the agent should describe the mass at the treated site and explain that recurrent tumor and delayed radiation injury are both possible, rather than simply call it progression. The history does not settle the diagnosis. It changes which conclusions are justified and what uncertainty the report needs to communicate.

![Timeline for SYN0056: radiosurgery in October 2016, the prior MRI on 2017-06-13, resection and a post-operative MRI in August 2017, head CTs on dexamethasone, and the current MRI on 2018-04-14. Comparing with the prior crosses the resection. Without the chart the report says the tumor core increased; with the chart it says the mass is new since the post-operative MRI and frames recurrence versus radiation necrosis.](img/treatment-timeline.svg)

## Step 2 — Copy the skills and data (~2 min)

From the workspace root:

```bash
cp -r chapters/chapter3-knowledge-sources/answer-key/. .
cp -r chapters/chapter3-knowledge-sources/data .
```

On Windows PowerShell:

```powershell
Copy-Item -Recurse -Force chapters\chapter3-knowledge-sources\answer-key\* .
Copy-Item -Recurse -Force chapters\chapter3-knowledge-sources\data .
```

That adds:

```
.github/skills/
  lookup-patient-history/       reads the chart and prior reports
  write-report-with-ehr/        writes the context-aware report
data/
  patients/SYN0056.json         the chapter's patient (SYN0062 for extra credit)
  reports/SYN0056_002.md        the prior report
  images/SYN0056_006.nii.gz     current MRI, 2018-04-14 (same scan as Chapter 2)
  images/SYN0056_002.nii.gz     prior MRI, 2017-06-13 (same scan as Chapter 2)
```

The two skills:

- **`lookup-patient-history`**: pure data. Infers the patient ID from the image file name, reads the JSON chart, and inlines the prior report. It makes no tool calls. In a real deployment, this is the skill that would call your EHR.
- **`write-report-with-ehr`**: calls `lookup-patient-history`, picks the most recent prior with a retained image, runs `write-imaging-factsheet` on the current and prior scans, then writes a comparison-aware report. It reads change against procedures and treatments between the exams, and answers the order.

No MCP changes: the report skill uses the four tools from Chapter 2.

Reload the VS Code window (`Developer: Reload Window`) so the new skills register.

## Step 3 — Run the agent (~3 min)

Start a new chat with **Radiology Assistant** and ask:

```
/write-report-with-ehr Please write a radiology report for data/images/SYN0056_006.nii.gz.
```

Watch the trace:

1. `lookup-patient-history` returns a `PATIENT RECORD` block with the diagnosis, procedures, imaging history, and the `_002` report inlined.
2. `write-imaging-factsheet` segments and cleans both scans and calls `describe_lesions` once with the prior.
3. Two trace sections come before the report:
   - `## Prior information used`: what the agent leaned on.
   - `## Clinical details used in the report`: each report phrase paired with its record field or descriptor ID.
4. The `<confidence>` and `<report>` blocks come last.

Check the report:

- **INDICATION** comes from the `_006` order.
- **COMPARISON** names the 2017-06-13 MRI (`SYN0056_002`) and the other relevant studies.
- **FINDINGS** quotes the factsheet's diameters and volumes, says the comparison crosses the 2017-08-17 resection, describes the mass against the post-operative baseline, notes the dexamethasone, and attributes the midline shift to the head CTs.
- **IMPRESSION** answers the order: it frames recurrent tumor versus radiation necrosis rather than calling progression.

## Step 4 — Compare with your Chapter 2 report (~2 min)

Put this report next to the one from Chapter 2, Step 7: the same two scans, measured by the same tools. If you no longer have it, run:

```
/write-report-measured Please write a radiology report for data/images/SYN0056_006.nii.gz, comparing with the prior data/images/SYN0056_002.nii.gz.
```

What you should see:

- ✅ Chapter 2 reports the tumor-core change since 2017-06-13 as an increase. Chapter 3 says the comparison crosses the resection and that the mass is new since the post-operative MRI.
- ✅ Chapter 3's **INDICATION** comes from the order; Chapter 2's is `Not provided.`
- ✅ Chapter 3's **IMPRESSION** answers the order's question; Chapter 2's lists findings.
- ✅ Chapter 3 places the mass in the right parietal lobe with support from the chart; in Chapter 2, location was the agent's own read.
- ✅ Chapter 3 mentions the steroids and the CT midline shift; Chapter 2 has no way to know about them.
- ⚠️ The measurements are the same, apart from small run-to-run differences in the model's output. The improvement comes from context, not a smarter model or new tools. 

> **Improving tool and measurement compliance.** By this point the agent has many skills and tools, and smaller models may start to break down: ignoring instructions, skipping tool calls, or calling tools incorrectly. If you see this behavior, try using the [improved-compliance answer key](answer-key-improved-compliance) to set up a new agent and update the skills it uses. Observe the changes and how editing instructions can help you achieve improvements without bringing in more expensive models.

## (Optional) Extra credit

Pick one:

1. **Remove the surgery.** In your copy of `data/patients/SYN0056.json`, delete the craniotomy from `procedures` and study `_003` from `imaging_studies`. Rerun Step 3. Does the report now call the change growth? Should it?
2. **Another patient.** Run `/write-report-with-ehr Please write a radiology report for data/images/SYN0062_001.nii.gz.` (renal cell carcinoma, untreated metastases, on an anticoagulant). Its priors are summaries only, so the factsheet has no change lines and the report compares in words. Confirm the lookup keys off the file name, not a hardcoded ID.
3. **Two ways to measure.** The prior report measured the 2017 mass at 4.3 × 3.4 × 4.3 cm; `describe_lesions` measured the same scan at about 4.4 × 3.5 cm. Open the 2017 `.measurements.png` in `audit-log/` and consider why a radiologist's caliper reading and a geometric measurement on a mask can differ.
4. **FHIR shape.** Refactor `lookup-patient-history` to consume a minimal FHIR bundle (`Patient`, `Condition`, `Procedure`, `MedicationStatement`, `ImagingStudy`, `DiagnosticReport`) instead of the flat JSON. The report skill shouldn't need to change; that's the point.
5. **Look at the audit log.** Chapter 3 saved its files in new folders, `audit-log/data/images/SYN0056_006/` and `SYN0056_002/`, because the image paths differ from Chapter 2's even though the scans are the same. Open its factsheet next to Chapter 2's in `audit-log/samples/mri-brain-lesions/case-056/2018-04-14/series-0902/` and compare the numbers. Small differences come from the model's output, not the code.

## What you should have at the end

- [ ] Skimmed `SYN0056.json` and the `_002` report, and know which fields the report should lean on
- [ ] `lookup-patient-history` and `write-report-with-ehr` under `.github/skills/`
- [ ] `data/patients/`, `data/reports/`, and `data/images/` at the workspace root
- [ ] A Chapter 3 report on `_006` whose COMPARISON names `_002`, whose numbers match the factsheet, which accounts for the resection between the exams, and whose impression answers the order
- [ ] A side-by-side comparison with your Chapter 2 report on the same scans

If you got stuck, the completed version of every file is in `chapters/chapter3-knowledge-sources/answer-key/`.

## What's next

You've built the full loop: an agent, a structured report skill, a segmentation foundation model, measurement code, and patient context. These patterns generalize:

- **Real EHRs.** Swap the synthetic `data/patients/*.json` for a FHIR or HL7 client. The `lookup-patient-history` skill stays; only the data source changes.
- **More targets and modalities.** MedImageParse segments from text prompts across CT, MRI, X-ray, ultrasound, pathology, and more. Same MCP server pattern, different models and prompts in `models.json`.
- **More code behind tools.** Anything deterministic, such as measurement, change calculation, and volumetry, belongs in code behind an MCP tool, not in a prompt.
