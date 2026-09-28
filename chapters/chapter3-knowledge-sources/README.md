# Chapter 3 — Connect a knowledge source to the agent

**Time budget: ~10 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Chapter 2 complete, with the `medimageinsight` MCP server wired up and both `zeroshot_classify` and `adapter_classify` working.

## Overview

Chapter 2 gave the agent a calibrated vision call. But a real chest X-ray read is never just "look at the pixels" — it depends on **patient context**: indication, prior studies, indwelling devices, what changed since the last film. In this chapter you give the agent access to a synthetic patient record and a comparison-aware report skill, then run the same image through it and watch the report change.

There's nothing to write in this chapter. Two skills and a small data folder; copy them in, run, observe. The takeaway is qualitative — same image, same adapter, *different* report once the agent can see the chart.

**Steps:**
1. Skim the patient record so you know what context is available. (~2 min)
2. Copy the two skills and the `data/` folder into your workspace. (~3 min)
3. Run the agent on the current study and read the output. (~3 min)
4. Compare to a Chapter 2-style read of the same image. (~2 min)

> The patient record under `data/patients/` is **fictional**, generated for the workshop, and **not for clinical use**. The image IDs (`00026132_*`) are real NIH ChestX-ray14 files, but the chart wrapped around them is invented.

## Step 1 — Skim the patient record (~2 min)

Open [data/patients/00026132.json](data/patients/00026132.json) and skim. The shape is intentionally ad-hoc (not FHIR) — flat fields, easy to read.

Things to notice:

- **Admission HPI** — community-acquired pneumonia with bilateral parapneumonic effusions.
- **`procedures`** — left pigtail placed without issue on day 3; right pigtail attempted, **aborted with iatrogenic right pneumothorax and sub-Q emphysema**; right 28F chest tube placed day 4.
- **`indwelling_devices`** — what should be on the current film. The agent should *confirm* their position, not call them new.
- **`imaging_studies`** — `_000`–`_003`. Only `_003` has a retained image and full report; earlier studies are listed but their image bytes were dropped from this excerpt.
- **`last_record_entry_note`** — the chart stops at the day-4 chest tube. Anything that happened after, the agent doesn't know about.

The current study you're going to read is `_011`. The chart's most recent prior is `_003`. That gap is the point — the agent has to anchor "what changed" against an older study, not a film from this morning.

## Step 2 — Copy the skills and data (~3 min)

From the workspace root:

```bash
# Two skills: one looks up the chart, one writes the report.
cp -r chapters/chapter3-knowledge-sources/answer-key/.github/skills/lookup-patient-history \
      .github/skills/
cp -r chapters/chapter3-knowledge-sources/answer-key/.github/skills/write-report-with-ehr \
      .github/skills/

# The synthetic chart, the prior report, and the two images.
mkdir -p data/patients data/reports data/images
cp chapters/chapter3-knowledge-sources/data/patients/00026132.json data/patients/
cp chapters/chapter3-knowledge-sources/data/reports/00026132_003.md  data/reports/
cp chapters/chapter3-knowledge-sources/data/images/00026132_*.png    data/images/
```

The two skills:

- **`lookup-patient-history`** — pure data. Takes an image path, infers the patient ID from the filename, reads the JSON, inlines the prior report. Zero tool calls. Notice that if you were to create a real-world agent that grounds its judgements in patient history - this is the skill where you would be calling tools to interface with your real-world Epic (or other EHR of your choice) deployment.
- **`write-report-with-ehr`** — the orchestrator. Calls `lookup-patient-history`, calls `adapter_classify` once on the current image, writes a comparison-aware report.

No MCP changes. The Chapter 2 server (`adapter_classify`) is the only tool the report skill calls.

Reload the VS Code window so the new skills register.

## Step 3 — Run the agent (~3 min)

Switch to **Radiology Assistant** and ask:

```
Use the write-report-with-ehr skill to write a report for
data/images/00026132_011.png.
```

Watch the trace. You should see:

1. `lookup-patient-history` invoked — returns the structured `PATIENT RECORD` block with HPI, devices, prior report inlined.
2. **One** call to `mcp_medimageinsig_adapter_classify` on `_011` (no re-scoring of the prior — the prior comes in as text from its report, not as a fresh classification).
3. The report itself, with two trace sections in front of it:
   - `## Prior information used` — what the agent actually leaned on.
   - `## Clinical details used in the report` — each report phrase paired with its EHR field or adapter call.
   - `<confidence>` + `<report>` block last.

The report should have a `COMPARISON: PA chest, ..., 00026132_003.` line, acknowledge the documented chest tubes by position rather than calling them new, and frame the impression around interval change.

## Step 4 — Compare to a Chapter 2 read (~2 min)

Run the **Chapter 2** skill on the same image for contrast:

```
Use the write-report-adapter skill to write a report for
data/images/00026132_011.png.
```

Same image, same adapter, no chart. Compare the two reports side by side.

What you should see:

- ✅ The Chapter 3 report has a **COMPARISON** section anchored to `_003`. Chapter 2 has none.
- ✅ Chapter 3 talks about the chest tubes as *expected* devices and confirms position. Chapter 2 may flag them as new findings.
- ✅ Chapter 3's **IMPRESSION** is change-first ("worsening despite drainage", "stable post-tube"). Chapter 2's is finding-first.
- ✅ The **INDICATION** in Chapter 3 reflects the actual admission HPI (CAP, bilateral effusions). Chapter 2 has no indication to anchor to.
- ⚠️ Notice that the *vision* call is identical. The improvement is the agent having the right context — not a smarter model. That's the lesson of the chapter.

## (Optional) Extra credit

Pick one:

1. **Break the chart and re-run.** Edit your copy of `data/patients/00026132.json` to remove `indwelling_devices`. Re-run Step 3. Does the agent now flag the chest tubes as new? Should it?
2. **Add a second patient.** Synthesize another `data/patients/<id>.json` for a different NIH patient ID, drop in an image with that prefix, and run the report skill on it. Confirm the lookup keys off the filename, not a hardcoded ID.
3. **FHIR shape.** Refactor `lookup-patient-history` to consume a minimal FHIR `Patient` + `Condition` + `AllergyIntolerance` + `MedicationStatement` bundle instead of the workshop's flat JSON. The report skill shouldn't need to change — that's the point.

## What you should have at the end

- [ ] Skimmed `00026132.json` and know which fields the report should lean on
- [ ] `lookup-patient-history` and `write-report-with-ehr` skills under `.github/skills/`
- [ ] `data/patients/00026132.json`, `data/reports/00026132_003.md`, and the two `00026132_*.png` images at the workspace root
- [ ] A Chapter 3 report run on `_011` that includes a `COMPARISON:` line anchored to `_003`, acknowledges the documented chest tubes, and frames the impression around interval change
- [ ] A side-by-side comparison against the Chapter 2 skill on the same image

If you got stuck, the completed version of every file is in `chapters/chapter3-knowledge-sources/answer-key/`.

## What's next

You've built the full loop: agent + structured report skill + vision foundation model (zero-shot and adapter) + patient context. These patterns generalize:

- **Real EHRs.** Swap the synthetic `data/patients/*.json` for a FHIR/HL7 client. The `lookup-patient-history` skill stays; only the data source changes.
- **More modalities.** MI2 covers CT, MRI, dermatology, pathology, retina. Same MCP server pattern, different label set or different adapter head.
- **Your own data.** The adapter training notebooks in Chapter 2's `extra-credit/` are a template — point them at your own labeled images and retrain.

MCP tools for new capabilities, skills for new behaviors, agent files to compose them. The harness doesn't change.
