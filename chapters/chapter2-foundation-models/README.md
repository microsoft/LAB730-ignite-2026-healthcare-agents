# Chapter 2 — Using foundation models with agents

**Time budget: ~40 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Chapter 1 complete, with `.github/agents/radiology-assistant.agent.md` and the `write-report-simple` skill under `.github/skills/` at your workspace root. A `.env` at the repository root holds `MIP_MODEL_ENDPOINT` and `MIP_MODEL_API_KEY`, and `uv run workshop/check_env.py` passes.

## Overview

In Chapter 1 the agent wrote tidier reports, but it still had to guess whether a lesion was there and could not measure it. In this chapter you connect **MedImageParse 3D**, a foundation model that segments whole MRI volumes from text prompts, through a small **MCP (Model Context Protocol) server**. Then you add tools that turn its mask into measurements, and a skill that collects those measurements into a factsheet.

![Chapter 2 pipeline: a brain MRI volume goes to MedImageParse 3D through segment, the mask goes to clean_segmentation and describe_lesions, and the descriptors go through the factsheet to write-report-simple. Each step saves its files in the image's audit-log folder.](img/segmentation-pipeline.svg)

| | Part 1: Segment | Part 2: Measure |
|---|---|---|
| Tools | `list_models`, `segment` | `clean_segmentation`, `describe_lesions` |
| What runs | MedImageParse 3D | Python on the mask and image geometry |
| Output | Tumor-component mask and film grids | Lesion IDs, volumes, diameters, change from a prior, factsheet |
| Question | Which tumor components are present? | How many lesions, how big, and how have they changed? |

Two design choices to notice:

- **Store compute-efficient segmentations.** A mask holds millions of voxels. `segment` saves it to disk and returns its path; the next tool reads the file.
- **Models return masks; code returns facts; the LLM writes words.** Each layer does the part it is reliable at.

Every file the tools write goes to `audit-log/` at your workspace root, in one folder per image: masks, review images, descriptors, and the factsheet. Open it at any point to see what the agent saw.

**Steps:**

0. Setup — copy the starter files. (~3 min)

**Part 1 — Segment**

1. Wire the `segment` tool. (~6 min)
2. Skim the segmentation skill. (~2 min)
3. Try it, then open the audit log. (~7 min)

**Part 2 — Measure**

4. Why measurements come from code. (~2 min)
5. Wire `clean_segmentation` and `describe_lesions`. (~4 min)
6. Skim the factsheet and measured-report skills. (~4 min)
7. Try it with a prior scan. (~10 min)

**(Optional) Extra credit.**

## Setup (~3 min)

Copy the starter files into your workspace root:

```bash
cp -r chapters/chapter2-foundation-models/starter/. .
```

On Windows PowerShell: `Copy-Item -Recurse -Force chapters\chapter2-foundation-models\starter\* .`

That adds the following at your workspace root. Your Chapter 1 agent and `write-report-simple` skill stay as they are:

```
.github/skills/
  write-report-segmentation/      Part 1 report skill (complete)
  write-report-measured/          Part 2 report skill (complete)
  write-imaging-factsheet/        Part 2 factsheet skill (complete)
    template/factsheet.md
mcp/medimageparse-server/
  server.py                       list_models works; three TODOs
  models.json                     model catalog: deployments and prompt views
  segmentation.py                 calls MedImageParse 3D, saves masks and film grids (read-only)
  lesions.py                      cleanup and descriptors (read-only)
  figures.py                      review images (read-only)
.vscode/
  mcp.json                        registers the server
```

The server reads `MIP_MODEL_ENDPOINT` and `MIP_MODEL_API_KEY` from the `.env` at the repository root, the same file `check_env.py` uses.

## Part 1 — Segment

### Step 1 — Wire the `segment` tool (~6 min)

Open `mcp/medimageparse-server/server.py`. The `list_models` wrapper already works: it delegates to a function in `segmentation.py` and reuses that function's docstring as the tool description. Replace the first TODO with the same pattern:

```python
@mcp.tool(description=segmentation.segment.__doc__)
def segment(image_path: str, model: str, prompts: list[str]) -> dict:
    return segmentation.segment(image_path, model, prompts)
```

Three things matter here:

- **Decorator.** `@mcp.tool(...)` registers the function with the server. Without it, the agent cannot see the tool.
- **Type hints.** MCP builds the tool's input schema from them. `image_path`, `model`, and `prompts` are required.
- **Docstring as description.** The agent reads `segment`'s docstring to learn which prompts to send and what comes back.

Save, then run `MCP: List Servers` from the command palette (`Ctrl/Cmd+Shift+P`). In the list that opens, select the `medimageparse` server, then select its **Start** icon.

> Open **View → Output → Agent Host** for the startup log.

Open `.github/agents/radiology-assistant.agent.md` and add `medimageparse/*` to the `tools:` list:

```yaml
tools: [execute, read, agent, browser, edit, search, web, todo, medimageparse/*]
```

In the same file, replace the Chapter 1 workflow step 2 (`Write the report with the write-report-simple skill`) so the agent prefers the tool-backed skills:

```markdown
2. **Write the report with a report skill.** If the user names a skill, use it. Otherwise use the most capable report skill whose tools are available: `write-report-measured` (`segment`, `clean_segmentation`, and `describe_lesions`), else `write-report-segmentation` (`segment` only), else `write-report-simple`. Return its output unchanged.
```

No further agent-file edit is needed in this chapter.

### Step 2 — Skim the segmentation skill (~2 min)

Open `.github/skills/write-report-segmentation/SKILL.md`:

- **Frontmatter `description`** tells the agent to use this skill when `segment` is available but the Part 2 tools are not.
- **Steps 1–2** call `list_models` and `segment` with the catalog's three tumor-component prompts (enhancing tumor, edema, necrotic core), then turn each `detected` flag into a present or absent finding.
- **Step 3** hands those findings to `write-report-simple` from Chapter 1, with no measurements: the raw mask is uncleaned, so the skill doesn't report its volumes.
- **Step 4** returns the report and the `audit_dir` where the tool saved its files.

### Step 3 — Try it (~7 min)

Start a new chat, select **Radiology Assistant**, and send the same image you used in Chapter 1:

```
/write-report-segmentation Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

If VS Code asks for permission to run the MCP tools, select **Allow All**.

> Segmentation might take a few minutes if the endpoint call needs retries.

Watch the trace: `list_models`, one `segment` call, then `write-report-simple` and the report. Every tumor component the report mentions should match a prompt that came back `detected: true`, and the size should still be qualitative.

Now open the folder the reply ends with, `audit-log/samples/mri-brain-lesions/case-056/2017-06-13/series-0018/`:

- `film-grid.png`: the axial slices on their own, anterior up and the patient's right on screen left.
- `<mask stem>.film-grid.png`: the same slices with the mask overlaid. Compare it with the image. Look for small colored regions away from the main tumor; Part 2 drops the smallest of them before measuring.
- `<mask stem>.nii.gz` and `.json`: the mask and the model, deployment, and prompts that produced it.

> **Why this matters.** `write-report-simple` is unchanged from Chapter 1, and the agent file gained only a tool entry and an updated workflow step. You added a vision capability by registering an MCP tool.

If the MCP server fails to start, make sure the workspace is trusted in VS Code (see [Troubleshooting](../../docs/troubleshooting.md#mcp-server-is-not-discovered)).

## Part 2 — Measure

A mask says which voxels are tumor. Turning that into "one lesion, 6.2 × 4.6 cm, tumor core up 112% since the prior" takes voxel spacing from the image header, 3D connected components, and geometry. Deterministic code does that the same way every time, and you can test it. An LLM looking at the image cannot.

### Step 4 — Why measurements come from code (~2 min)

Brain tumors are followed by size: the tumor-core volume, and on axial slices the **longest diameter** of the tumor core and the **longest diameter perpendicular to it**. Whether a tumor is growing comes down to comparing those numbers between scans, so they have to be real.

- **Millimeters aren't in the pixels.** Voxel spacing comes from the NIfTI header; `describe_lesions` reads it.
- **Masks need cleanup first.** `clean_segmentation` merges tumor-core pieces within 5 mm into one lesion and drops regions under 0.1 mL, then saves the cleaned mask and lesion IDs.
- **Descriptors are facts, not interpretation.** `describe_lesions` reports counts, volumes, diameters, and change from a prior. It assigns no side or anatomy, and it lists its limitations.

### Step 5 — Wire `clean_segmentation` and `describe_lesions` (~4 min)

Replace the remaining two TODOs in `server.py`:

```python
@mcp.tool(description=lesions.clean_segmentation.__doc__)
def clean_segmentation(mask_path: str, merge_distance_mm: float = 5.0,
                       min_lesion_ml: float = 0.1, min_edema_ml: float = 0.1) -> dict:
    return lesions.clean_segmentation(mask_path, merge_distance_mm, min_lesion_ml, min_edema_ml)


@mcp.tool(description=lesions.describe_lesions.__doc__)
def describe_lesions(clean_path: str, prior_clean_path: str | None = None) -> dict:
    return lesions.describe_lesions(clean_path, prior_clean_path)
```

Parameters with defaults become optional inputs in the tool schema. The tools chain through file paths: `segment` returns `mask_path`, `clean_segmentation` returns `clean_path`, and `describe_lesions` reads it.

Reload the server and confirm all four tools appear under **medimageparse**.

### Step 6 — Skim the factsheet and measured-report skills (~4 min)

Open `.github/skills/write-imaging-factsheet/SKILL.md` and its `template/factsheet.md`. The skill segments, cleans, and describes each scan, then fills the template. Every line cites a descriptor ID such as `[L1.bidimensional]`, and values are copied, never computed.

Then open `.github/skills/write-report-measured/SKILL.md`. It invokes the factsheet skill, then passes the factsheet's numbers to `write-report-simple` as `measurements`, copied verbatim. Lesion IDs are ranked separately in each scan, so change is reported for totals, not matched lesions.

### Step 7 — Try it with a prior scan (~10 min)

In a new chat with **Radiology Assistant**, ask for the follow-up scan and give the Part 1 scan as the prior:

```
/write-report-measured Please write a radiology report for samples/mri-brain-lesions/case-056/2018-04-14/series-0902.nii.gz, comparing with the prior samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

Watch the trace: `write-report-measured`, then `write-imaging-factsheet` calling `segment` and `clean_segmentation` for each scan and `describe_lesions` once, then `write-report-simple`.

Open the 2018 folder, `audit-log/samples/mri-brain-lesions/case-056/2018-04-14/series-0902/`:

- `<mask stem>.factsheet.md`: open the preview (`Ctrl/Cmd+Shift+V`) to see the facts with the film grids and measurement image.
- `<mask stem>.measurements.png`: each lesion on its measured slice, with both diameters drawn.
- `<mask stem>.descriptors.json`: the source of every factsheet line.

Then check the report:

- Diameters, volumes, and percent changes match the factsheet lines exactly.
- COMPARISON names the 2017 exam.
- Any side or location is the agent's own reading. Check it against the overlay film grid: the patient's right is on screen left.

> MedImageParse output varies slightly between calls, so small volumes, mostly edema, can differ from run to run. The code is deterministic: the same mask always gives the same descriptors.

## (Optional) Explore the audit log

Open `audit-log/samples/mri-brain-lesions/case-056/2018-04-14/series-0902/`. Each step left files here (`<stem>` is the shared prefix that starts with `mip3d-mri-brain-lesion`):

| File | Written by | What it holds |
|---|---|---|
| `film-grid.png` | `segment` | The scan alone, axial slices |
| `<stem>.film-grid.png` | `segment` | The raw mask on the same slices |
| `<stem>.nii.gz`, `<stem>.json` | `segment` | The mask, and the model and prompts that made it |
| `<stem>.clean.*`, `<stem>.lesions.*` | `clean_segmentation` | Cleaned mask, lesion IDs, and cleanup settings |
| `<stem>.descriptors.json` | `describe_lesions` | Every number with its ID, unit, and rule |
| `<stem>.measurements.png` | `describe_lesions` | Each lesion on its measured slice |
| `<stem>.factsheet.md` | the agent | The only file the language model wrote |

Things to try:

1. Open the two film grids side by side. In the overlay, red is enhancing tumor, blue is edema, and green is the necrotic core. Look for colored regions you would not call tumor.
2. In `.descriptors.json`, find `L1.bidimensional` and match its `slice_index` to the `z` label on the film grid and the measurement image.
3. Read the `limitation` entries: what the descriptors cannot tell you, such as side and anatomy.
4. Pick one factsheet line and find the descriptor it cites. Every other file here was written by code, not by the language model.

## (Optional) Extra credit

1. **Change the cleanup.** Ask the agent to rerun `clean_segmentation` on the 2018 mask with `min_edema_ml` set to 1.0, then `describe_lesions` without a prior. Compare the edema components. The parameters are saved in `.clean.json`, and the rerun replaces that scan's cleaned mask and descriptors.
2. **Try another view.** Ask the agent to call `segment` with the `whole-tumor` view from `list_models` and compare its `volume_ml` with `total.volume.whole_tumor` in the descriptors.
3. **Factsheet only.** Run `/write-imaging-factsheet` on the 2018 scan with the 2017 prior and read the factsheet without a report.

## What you should have at the end

- [ ] `segment`, `clean_segmentation`, and `describe_lesions` wired in `server.py` and visible in the tool picker
- [ ] `medimageparse/*` in the agent's `tools:` list, and the workflow's report step updated
- [ ] A Part 1 report whose tumor components each match a detected label, with qualitative size
- [ ] A Part 2 report whose numbers match the factsheet, with the 2017 exam as the comparison
- [ ] `audit-log/` folders for both scans, with film grids, masks, descriptors, the measurement image, and the factsheet

If you got stuck, the completed version of every file is in `chapters/chapter2-foundation-models/answer-key/`.

## What's next

[Chapter 3](../chapter3-knowledge-sources/README.md) adds patient context: history and prior reports that change how the findings are interpreted.
