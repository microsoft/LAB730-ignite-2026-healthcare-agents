# Chapter 1 — Simple agent with a skill

**Time budget: ~20 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Workshop-level setup from the repo root [`README.md`](../../README.md) complete — VS Code with the GitHub Copilot Chat extension signed in, this repo cloned and open as your workspace, and `uv sync` run from the repo root. When you open the workspace in VS Code, confirm that it's a **trusted workspace** when prompted.

## Overview

In this chapter you will build a minimal "radiology assistant" agent inside VS Code that uses a general-purpose LLM (no specialized foundation model yet) to generate a structured report from a brain MRI image. The point is to feel how *cheap* and *easy* it is to compose an agent from skills — and to see, by the end, that a generic LLM is **not** clinically reliable on its own.

We start with a very simple agent, without any skills, and progress by adding a skill to start seeing better conformance.

A "Radiology Assistant" agent built on a generic LLM will happily produce a brain MRI report, but it is not clinically reliable: section names drift run-to-run, hedging language is inconsistent, confidence is never stated — and, worst of all for brain lesions, it will quote lesion sizes in millimeters that it has no way to measure. In this chapter you build that bare agent, watch it drift, then close the gap by adding a single **skill** — a structured, reusable instruction packet that gives the agent a fixed report template, phrasing discipline, a "no invented numbers" rule, and calibrated confidence buckets. By the end you'll see the same agent produce a consistent report on the same image.

**Steps:**

0. Setup — copy the starter agent file to your workspace. (~1 min)
1. See the gap — run the bare agent and note where structure drifts and numbers appear from nowhere. (~5 min)
2. Build the skill — fill in the `SKILL.md` TODOs. (~10 min)
3. Activate it — point the agent's workflow at the skill. (~2 min)
4. (Optional) Phrase bank additions.

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
Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

> Remember, the agent **only accepts file paths**. Don't drag the image into chat or use the paperclip; if you do, it'll refuse.

When VS Code first asks for permission to run a tool, select **Allow All**.

Run it on 2-3 different images. Note a few things:

- **Output drift.** Section names drift, structure is unpredictable, and confidence isn't called out separately.
- **Inconsistency.** Run it a few times and note how the output changes. The code the agent writes to read the image also differs from run to run, sometimes significantly.
- **Sizes.** The agent has pixels, not millimeters: no pixel spacing and no mask. If the report quotes a lesion size like "3.4 × 2.8 cm", that number is a guess dressed up as a measurement. If it doesn't, try asking it to measure the lesion.
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

Open `SKILL.md`. Each TODO is tagged with an anchor name. For each one: read the teaching note below, look at the placeholder in the file, then paste from [suggested-changes.md](suggested-changes.md) or write your own:

- [ ] **Fill the `description` TODO.**

  The agent matches this string against the task at hand to decide whether to invoke the skill. Specific beats categorical — vague descriptions get ignored.

  → [Suggested text](suggested-changes.md#description)

- [ ] **Fill the `argument-hint` TODO.**

  `argument-hint` declares optional inputs other agents or later chapters may pass in. We won't pass any in Chapter 1, but declaring them now makes the skill an interface with a contract, not just a prompt. In Chapter 2 you'll call it with real outputs from a segmentation model (`findings`) and a measurement tool (`measurements`).

  → [Suggested text](suggested-changes.md#argument-hint)

- [ ] **Fill the `one-liner` TODO.**

  This one-sentence description is for humans reading the file — a different audience from the frontmatter `description`, which is for the agent's routing logic.

  → [Suggested text](suggested-changes.md#one-liner)

- [ ] **Fill the `inputs` TODO.**

  Declaring a field in `argument-hint` isn't enough — the body must tell the agent how to use it. This section sets the priority order so the agent doesn't have to guess, and makes tool-supplied `measurements` authoritative.

  → [Suggested text](suggested-changes.md#inputs)

- [ ] **Fill the `how-to-use` TODO.**

  The skill ships with supporting files. `template/mri-brain-template.md` and `references/phrase-bank.md` are already complete — the skill body just references them so the agent reads them on demand.

  → [Suggested text](suggested-changes.md#how-to-use)

- [ ] **Fill the `style-rules` TODO.**

  When the agent has options, the skill picks one and names it. These rules close the gaps that cause run-to-run drift in hedging language and sentence structure — and add two rules specific to brain lesions: **numbers come from tools only**, and **laterality is the patient's**.

  → [Suggested text](suggested-changes.md#style-rules)

- [ ] **Fill the `output-format` TODO.**

  Machine-readable output needs a verbatim template, not a description of one. The literal tags let downstream steps extract the confidence value without fragile string matching.

  → [Suggested text](suggested-changes.md#output-format)

## Step 3 — Activate it (~2 min)

The skill files exist, but nothing happens yet. Open the workspace-root agent file you copied during Setup:

```
.github/agents/radiology-assistant.agent.md
```

Find the `<workflow>` block. Replace steps 2 and 3 ("Analyze the image", "Draft the report") with one step that calls the skill:

→ [Suggested wording](suggested-changes.md#agent-workflow)

Start a new chat and run the Step 1 prompt on the same image, this time naming the skill:

```
/write-report-simple Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

The output should now:
- Use EXAM, INDICATION, COMPARISON, TECHNIQUE, FINDINGS, and IMPRESSION in order, with a blank line between sections and text on the first four header lines
- Have one prose paragraph for FINDINGS and numbered IMPRESSION statements, one per line
- Open with `<confidence>...</confidence>` on its own line, then `<report>...</report>`
- Describe lesion size qualitatively ("large", "moderate") instead of quoting invented millimeters
- Borrow phrasings you can find in `references/phrase-bank.md`

If it still looks like Step 1, the agent didn't pick up the skill. Check: directory name = `write-report-simple` exactly, all three files exist, and the workflow step names `write-report-simple`. It also helps to start a new chat session.

Now try another image:

```
/write-report-simple Please write a radiology report for samples/mri-brain-lesions/case-062/2021-06-25/series-0007.nii.gz.
```

Read each report against your own impression. Where does it go right? Where does it go wrong? Notice that the skill made the agent *honest* about size — but it still can't tell you *how big* the lesion is. That's Chapter 2.

> **Ways skills get invoked.** Here the agent's workflow names `write-report-simple`, so the agent calls it for every report. Without that step, an agent can still pick up a skill automatically when its `description` matches the request, or you can name it with `/<skillname>` (`/write-report-simple Please write a radiology report for …`). Explicit is useful when a skill's description is ambiguous or when several skills could plausibly handle the request. Typing `/` in the chat input lists the registered skills, which is a good way to check that yours was picked up.

Takeaway: a general-purpose LLM looking at pixels is not clinically reliable; a small skill restores the structure, phrasing discipline, and stated confidence the workflow needs — and stops it from inventing measurements. It can't *add* the measurements, though.

## (Optional) Step 4 — Extra credit

**Add to the phrase bank.** Pick a finding the bank doesn't cover well (for example, a specific white matter lesion pattern or an extra-axial collection) and add 2–3 example phrasings (positive / possible / negative) under a new section in `references/phrase-bank.md`. Start a fresh chat, re-run `/write-report-simple Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.`, and see whether the agent borrows your wording.

## What you should have at the end

- [ ] `.github/skills/write-report-simple/{SKILL.md, template/mri-brain-template.md, references/phrase-bank.md}`
- [ ] All TODOs in `SKILL.md` filled in: `description`, `argument-hint`, `one-liner`, `inputs`, `how-to-use`, `style-rules`, `output-format`
- [ ] Updated `.github/agents/radiology-assistant.agent.md` with a workflow step that calls `write-report-simple`
- [ ] An "after" report from Step 3 you can put next to the "before" from Step 1

If you got stuck, the completed version of every file is in `chapters/chapter1-simple-agent/answer-key/`.

## What's next

In Chapter 2 you'll give the agent **eyes and a ruler**. You'll wire **MedImageParse** — a prompt-based medical image segmentation foundation model — into the agent through a custom MCP server, then add a measurement tool that turns its lesion masks into millimeters. Every lesion in the report will then trace back to an actual mask, and every size to actual code, instead of the LLM guessing from pixels.