# Chapter 3 — Connect a knowledge source to the agent

**Time budget: ~10 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Chapter 2 complete, with the `medimageparse` MCP server wired up and both `segment_lesions` and `measure_lesions` working.

> 🚧 **Placeholder — PNG export and MedImageParse integration pending.** The patient images for this chapter come from MU-Glioma-Post `PatientID_0014`, but the PNG slices haven't been exported yet (see [data/images/README.md](data/images/README.md)). The Chapter 2 tools are still stubs. The chart, the prior report, and both skills are complete, but the chart and prior report still need to be brought in line with the real images.

## Overview

Chapter 2 gave the agent a grounded, measured read. But a brain tumor follow-up read is never just "look at the pixels" — it depends on **patient context**: the diagnosis, the surgery, when radiation finished, and what the lesion measured last time. In this chapter you give the agent access to a synthetic patient record and a comparison-aware report skill, then run the same image through it and watch the report change.

There's nothing to write in this chapter. Two skills and a small data folder; copy them in, run, observe. The takeaway is qualitative — same image, same tools, *different* report once the agent can see the chart.

**Steps:**
1. Skim the patient record so you know what context is available. (~2 min)
2. Copy the two skills and the `data/` folder into your workspace. (~3 min)
3. Run the agent on the current study and read the output. (~3 min)
4. Compare to a Chapter 2-style read of the same image. (~2 min)

> The patient record under `data/patients/` is **fictional**, generated for the workshop, and **not for clinical use**.

## Step 1 — Skim the patient record (~2 min)

Open [data/patients/SYN0417.json](data/patients/SYN0417.json) and skim. The shape is intentionally ad-hoc (not FHIR) — flat fields, easy to read.

Things to notice:

- **`diagnosis`** — glioblastoma (an aggressive primary brain tumor) in the left frontal lobe.
- **`procedures`** — subtotal resection on 2026-05-19. Some enhancing tumor was **deliberately left** along the back wall of the cavity to protect language and motor areas.
- **`treatments`** — chemoradiation finished on **2026-07-24**; adjuvant chemotherapy started 2026-08-24.
- **`expected_post_treatment_findings`** — what *should* be on the current scan: the resection cavity and post-treatment change. The agent should describe these as expected, not call them new.
- **`imaging_studies`** — `_000`–`_002`. Only `_002` has a retained image and full report, including the measurement the agent will compare against.
- **`pending_orders`** — the current study `_003`, ordered **8 weeks after completion of chemoradiation**.
- **`last_record_entry_note`** — the chart stops at the `_003` order. The agent doesn't know anything that happened after.

The current study you're going to read is `_003`. The chart's most recent report is `_002`, four weeks earlier.

> **Why the treatment dates matter.** For a few months after brain radiation, the treated area can swell and enhance more on MRI even when the tumor isn't growing — this is called *pseudoprogression*. The same increase in size that would mean "the tumor is growing" six months after treatment means "watch and re-scan" eight weeks after. The pixels can't tell those two apart; the chart can.

![Timeline for SYN0417: diagnosis MRI, surgery, chemoradiation, the prior MRI at 25 × 20 mm, and the current MRI 8 weeks after radiation, inside the window where growth may be treatment effect. Without the chart the report states only today's size; with the chart it compares against the prior and frames the change.](img/treatment-timeline.svg)

## Step 2 — Copy the skills and data (~3 min)

From the workspace root:

```bash
# Two skills: one looks up the chart, one writes the report.
cp -r chapters/chapter3-knowledge-sources/answer-key/.github/skills/lookup-patient-history \
      .github/skills/
cp -r chapters/chapter3-knowledge-sources/answer-key/.github/skills/write-report-with-ehr \
      .github/skills/

# The synthetic chart, the prior report, and the two images with their sidecars.
mkdir -p data/patients data/reports data/images
cp chapters/chapter3-knowledge-sources/data/patients/SYN0417.json data/patients/
cp chapters/chapter3-knowledge-sources/data/reports/SYN0417_002.md data/reports/
cp chapters/chapter3-knowledge-sources/data/images/SYN0417_*       data/images/
```

> 🚧 **Placeholder.** Until the images land, the last `cp` finds nothing to copy.

The two skills:

- **`lookup-patient-history`** — pure data. Takes an image path, infers the patient ID from the filename, reads the JSON, inlines the prior report. Zero tool calls. Notice that if you were to create a real-world agent that grounds its judgements in patient history - this is the skill where you would be calling tools to interface with your real-world Epic (or other EHR of your choice) deployment.
- **`write-report-with-ehr`** — the orchestrator. Calls `lookup-patient-history`, calls `segment_lesions` and `measure_lesions` once each on the current image, writes a comparison-aware report.

No MCP changes. The Chapter 2 server (`segment_lesions` + `measure_lesions`) is all the report skill calls.

Reload the VS Code window so the new skills register.

## Step 3 — Run the agent (~3 min)

Switch to **Radiology Assistant** and ask:

```
Use the write-report-with-ehr skill to write a report for
data/images/SYN0417_003.png.
```

Watch the trace. You should see:

1. `lookup-patient-history` invoked — returns the structured `PATIENT RECORD` block with diagnosis, treatments, and the `_002` report inlined.
2. **One** call to `mcp_medimageparse_segment_lesions` on `_003` (no re-segmenting the prior — the prior comes in as text from its report, not as a fresh segmentation).
3. **One** call to `mcp_medimageparse_measure_lesions` on the enhancing-tumor mask.
4. The report itself, with two trace sections in front of it:
   - `## Prior information used` — what the agent actually leaned on.
   - `## Clinical details used in the report` — each report phrase paired with its EHR field or tool call.
   - `<confidence>` + `<report>` block last.

The report should have a `COMPARISON: MRI brain with and without contrast, 2026-08-21, SYN0417_002.` line, quote the current measurement next to the prior one (`now … mm, previously 25 × 20 mm`), describe the resection cavity as an expected post-surgical finding, and frame any increase in light of the treatment timeline — treatment-related change versus progression — rather than calling progression outright.

## Step 4 — Compare to a Chapter 2 read (~2 min)

Run the **Chapter 2** skill on the same image for contrast:

```
Use the write-report-measured skill to write a report for
data/images/SYN0417_003.png.
```

Same image, same tools, no chart. Compare the two reports side by side.

What you should see:

- ✅ The Chapter 3 report has a **COMPARISON** section anchored to `_002`. Chapter 2 has none.
- ✅ Chapter 3 puts the current and prior measurements side by side. Chapter 2 has only today's — it can't say whether the lesion grew.
- ✅ Chapter 3 describes the resection cavity as an *expected* post-surgical finding. Chapter 2 may describe it as a cystic or necrotic lesion.
- ✅ Chapter 3's **IMPRESSION** is change-first and reads the change against the treatment timeline. Chapter 2's is finding-first.
- ✅ The **INDICATION** in Chapter 3 reflects the actual order (8 weeks after chemoradiation). Chapter 2 has no indication to anchor to.
- ⚠️ Notice that the *tool calls* are identical. The improvement is the agent having the right context — not a smarter model. That's the lesson of the chapter.

## (Optional) Extra credit

Pick one:

1. **Move the clock.** Edit your copy of `data/patients/SYN0417.json` so the `_003` order reads "6 months after completion of chemoradiation" (and shift the `treatments` dates to match). Re-run Step 3. Does the impression stop hedging about treatment-related change? Should it?
2. **Add a second patient.** Synthesize another `data/patients/<id>.json`, drop in an image named `<id>_<index>.png` with its sidecar, and run the report skill on it. Confirm the lookup keys off the filename, not a hardcoded ID.
3. **Let code do the arithmetic.** The report quotes both measurements but never computes the change — LLMs shouldn't do math you'll act on. Add a `compare_measurements` tool to the MCP server that returns the percent change between two bidimensional measurements, and have `write-report-with-ehr` cite it.
4. **FHIR shape.** Refactor `lookup-patient-history` to consume a minimal FHIR bundle (`Patient`, `Condition`, `Procedure`, `MedicationStatement`, `ImagingStudy`, `DiagnosticReport`) instead of the workshop's flat JSON. The report skill shouldn't need to change — that's the point.

## What you should have at the end

- [ ] Skimmed `SYN0417.json` and know which fields the report should lean on
- [ ] `lookup-patient-history` and `write-report-with-ehr` skills under `.github/skills/`
- [ ] `data/patients/SYN0417.json`, `data/reports/SYN0417_002.md`, and the `SYN0417_*` images at the workspace root
- [ ] A Chapter 3 report run on `_003` that includes a `COMPARISON:` line anchored to `_002`, puts current and prior measurements side by side, treats the resection cavity as expected, and reads the change against the treatment timeline
- [ ] A side-by-side comparison against the Chapter 2 skill on the same image

If you got stuck, the completed version of every file is in `chapters/chapter3-knowledge-sources/answer-key/`.

## What's next

You've built the full loop: agent + structured report skill + segmentation foundation model + measurement code + patient context. These patterns generalize:

- **Real EHRs.** Swap the synthetic `data/patients/*.json` for a FHIR/HL7 client. The `lookup-patient-history` skill stays; only the data source changes.
- **More targets and modalities.** MedImageParse segments from text prompts across CT, MRI, X-ray, ultrasound, pathology, and more; MedImageParse 3D takes whole volumes. Same MCP server pattern, different prompts.
- **More code behind tools.** Anything deterministic — measurement, change calculation, volumetry — belongs in code behind an MCP tool, not in a prompt.

MCP tools for new capabilities, skills for new behaviors, agent files to compose them. The harness doesn't change.