# Chapter 1 — Simple agent with a skill

**Time budget: ~20 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Workshop-level setup from the repo root [`README.md`](../../README.md) complete — VS Code with the GitHub Copilot Chat extension signed in, this repo cloned and open as your workspace, and `uv sync` run from the repo root.

## Overview

In this chapter you will build a minimal "radiology assistant" agent inside VS Code that uses a general-purpose LLM (no specialized foundation model yet) to generate a structured report from a brain MRI image. The point is to feel how *cheap* and *easy* it is to compose an agent from skills — and to see, by the end, where a generic LLM **stops** being clinically reliable on its own.

We start with a very simple agent, without any skills, and progress by adding a skill to start seeing better conformance.

A "Radiology Assistant" agent built on a generic LLM will happily produce a brain MRI report, but it is not clinically reliable: section names drift run-to-run, hedging language is inconsistent, confidence is never stated — and, worst of all for brain lesions, it may quote lesion sizes in millimeters that it has no way to measure. In this chapter you build that bare agent, watch it drift, then start closing some of the gaps by adding a single **skill** — a structured, reusable instruction packet that gives the agent a fixed report template, phrasing discipline, a "no invented numbers" rule, and calibrated confidence buckets. By the end you'll see the same agent produce a consistent report on the same image, and read an eval table that quantifies the improvement.

**Steps:**

0. Setup — copy the starter agent file to your workspace. (~1 min)
1. See the gap — run the bare agent and note where structure drifts and numbers appear from nowhere. (~5 min)
2. Build the skill — fill in the `SKILL.md` TODOs. (~10 min)
3. Activate it — add one rule to the agent file. (~2 min)
4. See the numbers — read an eval table via `summarize-eval`. (~3 min)
5. (Optional) Phrase bank additions or your own mini-eval.

## Setup (~1 min)

Copy the starter agent file into your workspace `.github/agents/` so VS Code picks it up:

You can do it manually or use the command line script.
```bash
# from repo root
mkdir -p .github/agents
cp chapters/chapter1-simple-agent/starter/.github/agents/radiology-assistant.agent.md .github/agents/radiology-assistant.agent.md
```

Inspect the file and observe how it contains instructions constraining the agent, but doesn't have much specific radiological guidance.

From here on, edit `.github/agents/radiology-assistant.agent.md` at the workspace root, not the copy inside `starter/`. You'll add a rule to it in Step 3.

## Step 1 — See the gap (~5 min)

Open Copilot Chat. With the agent definition file in place you should be able to select our new agent. In the agent picker, switch to **Radiology Assistant**.

![The Radiology Assistant agent in the Copilot Chat agent picker](img/agent.png)

Send:

```
Please write a radiology report for samples/SYN0417_003.png.
```

> **Sample data.** The canonical brain MRI is a glioblastoma follow-up from MU-Glioma-Post (CC BY 4.0). The [axial PNG](../../samples/SYN0417_003.png) and its [sidecar](../../samples/SYN0417_003.json) are exported from the [source NIfTI volumes](../../samples/nifti/README.md). Complete DICOM and per-slice PNG series are also available; additional cases for `samples/extra/` are still to be selected. See [samples/README.md](../../samples/README.md).

> Remember, the agent **only accepts file paths**. Don't drag the image into chat or use the paperclip; if you do, it'll refuse.

Run it on 2-3 different images. Notice that section names drift, hedging is unpredictable, and confidence isn't called out separately. Then look closer at two things that matter for brain lesions:

- **Sizes.** Does the report quote a lesion size like "3.4 × 2.8 cm"? The agent has pixels, not millimeters — it has no pixel spacing and no mask. That number is a guess dressed up as a measurement.
- **Sides.** Brain MRI is displayed in radiological convention: the patient's *right* is on the image *left*. Check whether the agent put the lesion on the correct side.

Keep one of the outputs visible — you'll compare against it after Step 3.

## Step 2 — Build the skill (~10 min)

Skills live at `.github/skills/<skill-name>/`. Copy the starter into place:

```bash
cp -r chapters/chapter1-simple-agent/starter/.github/skills/write-report-simple .github/skills/
```

That gives you three files:

```
.github/skills/write-report-simple/
  SKILL.md                       ← the skill body — has TODOs you'll fill in below
  template/mri-brain-template.md ← report structure (already complete, take a look)
  references/phrase-bank.md      ← example wordings (already complete, take a look)
```

Open all three and skim. The skill **name** (frontmatter `name:` and the directory name) must match exactly.

Open `SKILL.md`. Each TODO is tagged with an anchor name. For each one: read the teaching note below, look at the placeholder in the file, then paste from [suggested-changes.md](suggested-changes.md) or write your own.

### Fill the `description` TODO

The agent matches this string against the task at hand to decide whether to invoke the skill. Specific beats categorical — vague descriptions get ignored.

→ [Suggested text](suggested-changes.md#description)

### Fill the `argument-hint` TODO

`argument-hint` declares optional inputs other agents or later chapters may pass in. We won't pass any in Chapter 1, but declaring them now makes the skill an interface with a contract, not just a prompt. In Chapter 2 you'll call it with real outputs from a segmentation model (`findings`) and a measurement tool (`measurements`).

→ [Suggested text](suggested-changes.md#argument-hint)

### Fill the `one-liner` TODO

This one-sentence description is for humans reading the file — a different audience from the frontmatter `description`, which is for the agent's routing logic.

→ [Suggested text](suggested-changes.md#one-liner)

### Fill the `inputs` TODO

Declaring a field in `argument-hint` isn't enough — the body must tell the agent how to use it. This section sets the priority order so the agent doesn't have to guess, and makes tool-supplied `measurements` authoritative.

→ [Suggested text](suggested-changes.md#inputs)

### Fill the `how-to-use` TODO

The skill ships with supporting files. `template/mri-brain-template.md` and `references/phrase-bank.md` are already complete — the skill body just references them so the agent reads them on demand.

→ [Suggested text](suggested-changes.md#how-to-use)

### Fill the `style-rules` TODO

When the agent has options, the skill picks one and names it. These rules close the gaps that cause run-to-run drift in hedging language and sentence structure — and add two rules specific to brain lesions: **numbers come from tools only**, and **laterality is the patient's**.

→ [Suggested text](suggested-changes.md#style-rules)

### Fill the `output-format` TODO

Machine-readable output needs a verbatim template, not a description of one. The literal tags let downstream steps and evals extract the confidence value without fragile string matching.

→ [Suggested text](suggested-changes.md#output-format)

## Step 3 — Activate it (~2 min)

The skill files exist, but nothing happens yet. Open the workspace-root agent file you copied during Setup:

```
.github/agents/radiology-assistant.agent.md
```

Find the `<rules>` block. Add the "use available skills" line as the first bullet:

→ [Suggested wording](suggested-changes.md#agent-rule)

Run the same prompt from Step 1 on the same image. The output should now:
- Use the four all-caps section headers in order
- Have bulleted Findings / numbered Impression
- Open with `<confidence>...</confidence>` on its own line, then `<report>...</report>`
- Describe lesion size qualitatively ("large", "moderate") instead of quoting invented millimeters
- Borrow phrasings you can find in `references/phrase-bank.md`

If it still looks like Step 1, the agent didn't pick up the skill. Check: directory name = `write-report-simple` exactly, all three files exist, and the rule line is in `<rules>`. It also helps to start a new chat session.

Now try it on a few different images. Read each report against your own impression. Where does it go right? Where does it go wrong? Notice that the skill made the agent *honest* about size — but it still can't tell you *how big* the lesion is. That's Chapter 2.

## Step 4 — See the numbers (~3 min)

At this point you might be wondering: I've seen how this agent performs on a few individual images, what about testing it on a larger set? Evaluating the accuracy of radiology report generation is a complex task on its own, involving careful design of reliable metrics. Learning how to compute and how to understand these metrics is beyond the scope of this workshop, however we would like to give you a general idea how it's done.

We run this step's agent (with and without the skill) on a stratified brain MRI evaluation set and score every report — lesion detection, laterality, and report quality — broken down by the agent's self-reported confidence. Results live at `eval-results/initial/` (no skill) and `eval-results/chapter1/` (with skill) at the workshop root.

> 🚧 **Placeholder — eval results pending.** The brain MRI evaluation set, metric suite, and result directories are being produced for Ignite 2026. Until they ship, the command below reports missing files. See [eval-results/README.md](../../eval-results/README.md) for the planned layout.

`summarize-eval` ships in `.github/skills/` — it parses the eval result files into a metrics-by-confidence-bucket table. We ship it pre-built so this chapter stays focused on writing the report skill.

**Open a fresh chat with no agent selected** (default "Agent", not Radiology Assistant). Ask:

```
/summarize-eval, compare these two evals:
baseline: eval-results/initial
candidate: eval-results/chapter1
```

> Note that this skill contains a Python script. The agent in your chat UI will ask for your permission to run the script to which you need to agree.

You'll get a markdown table with metrics as columns and confidence buckets as rows for each, plus a delta table. Look for two things: do scores improve across the board, and do the agent's self-reported `high` confidence cases really score better than `medium` ones — is its confidence calibrated?

> **Two ways skills get invoked.** In Step 3 the radiology agent picked up `write-report-simple` automatically because its `description` matched what you asked it to do — that's auto-by-context. Here you named the skill explicitly in your prompt with a /<skillname> syntax (`/summarize-eval compare ...`) — that's manual invocation. Both work; explicit is useful when a skill's description is ambiguous or when several skills could plausibly handle the request. Note how typing / in chat window shows a list of available skills - that is a good way to check if your skill has been registered properly.

Takeaway: a general-purpose LLM looking at pixels is not clinically reliable; a small skill restores the structure, phrasing discipline, and calibrated confidence the workflow needs — and stops it from inventing measurements. It can't *add* the measurements, though.

## (Optional) Step 5 — Extra credit

**Add to the phrase bank.** Pick a finding the bank doesn't cover well (for example, a specific white matter lesion pattern or an extra-axial collection) and add 2–3 example phrasings (positive / possible / negative) under a new section in `references/phrase-bank.md`. Re-run on a relevant image and see whether the agent borrows your wording.

## What you should have at the end

- [ ] `.github/skills/write-report-simple/{SKILL.md, template/mri-brain-template.md, references/phrase-bank.md}`
- [ ] All TODOs in `SKILL.md` filled in: `description`, `argument-hint`, `one-liner`, `inputs`, `how-to-use`, `style-rules`, `output-format`
- [ ] Updated `.github/agents/radiology-assistant.agent.md` with the "use available skills" rule
- [ ] An "after" report from Step 3 you can put next to the "before" from Step 1
- [ ] Ran `summarize-eval` against shipped results and read the comparison

If you got stuck, the completed version of every file is in `chapters/chapter1-simple-agent/answer-key/`.

## What's next

In Chapter 2 you'll give the agent **eyes and a ruler**. You'll wire **MedImageParse** — a prompt-based medical image segmentation foundation model — into the agent through a custom MCP server, then add a measurement tool that turns its lesion masks into millimeters. Every lesion in the report will then trace back to an actual mask, and every size to actual code, instead of the LLM guessing from pixels.