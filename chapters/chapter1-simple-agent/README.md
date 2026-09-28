# Chapter 1 — Simple agent with a skill

**Time budget: ~20 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Workshop-level setup from the repo root `Readme.md` complete — VS Code with the GitHub Copilot Chat extension signed in, this repo cloned and open as your workspace, and `uv sync` run from the repo root.

## Overview

In this chapter you will build a minimal "radiology assistant" agent inside VS Code that uses a general-purpose LLM (no specialized foundation model yet) to (a) generate a structured imaging report from a chest X-ray and (b) summarize the results of an evaluation run. The point is to feel how *cheap* and *easy* it is to compose an agent from skills — and to see, by the end, that a generic LLM is **not** clinically reliable on its own.

We start with a very simple agent, without any skills, and progress by adding a skill to start seeing better conformance. 

A "Radiology Assistant" agent built on a generic LLM will happily produce a chest X-ray report, but it is not clinically reliable: section names drift run-to-run, hedging language is inconsistent, and confidence is never stated. In this chapter you build that bare agent, watch it drift, then close the gap by adding a single **skill** — a structured, reusable instruction packet that gives the agent a fixed report template, phrasing discipline, and calibrated confidence buckets. By the end you'll see the same agent produce a consistent report on the same image, and read a pre-computed eval table that quantifies the improvement across 210 cases.

**Steps:**
- Setup — copy the starter agent file to your workspace. (~1 min)
1. See the gap — run the bare agent and note where structure drifts. (~5 min)
2. Build the skill — fill in the `SKILL.md` TODOs. (~10 min)
3. Activate it — add one rule to the agent file. (~2 min)
4. See the numbers — read a pre-computed eval table via `summarize-eval`. (~3 min)
5. (Optional) Phrase bank additions or your own mini-eval.

## Setup (~1 min)

Copy the starter agent file into your workspace `.github/agents/` so VS Code picks it up:

You can do it manually or use the command line script.
```bash
# from repo root
mkdir -p .github/agents
cp chapters/chapter1-simple-agent/starter/.github/agents/radiology-assistant.agent.md .github/agents/radiology-assistant.agent.md
```

Inspect the file and observe how it contains instructions constraining the agent, but doesn't have too many specific radiological guidance.

From here on, edit `.github/agents/radiology-assistant.agent.md` at the workspace root, not the copy inside `starter/`. You'll add a rule to it in Step 3.

## Step 1 — See the gap (~5 min)

Open Copilot Chat. With the agent definition file in place you should be able to select our new agent. In the agent picker, switch to **Radiology Assistant**.

![alt text](img/agent.png)

Send:

```
Please write a radiology report for samples/00026132_011.png.
```

> The workshop ships a canonical case at `samples/00026132_011.png`. Additional NIH 2017 samples are under `samples/extra/` (30 images) — swap one in later to see how output varies.

> Remember, the agent **only accepts file paths**. Don't drag the image into chat or use the paperclip; if you do, it'll refuse.

Run it on 2-3 different images. Notice that section names drift, hedging is unpredictable, and confidence isn't called out separately. Keep one of the outputs visible - you'll compare against it after Step 3.

## Step 2 — Build the skill (~10 min)

Skills live at `.github/skills/<skill-name>/`. Copy the starter into place:

```bash
cp -r chapters/chapter1-simple-agent/starter/.github/skills/write-report-simple .github/skills/
```

That gives you three files:

```
.github/skills/write-report-simple/
  SKILL.md                       ← the skill body — has TODOs you'll fill in below
  template/cxr-template.md       ← report structure (already complete, take a look)
  references/phrase-bank.md      ← example wordings (already complete, take a look)
```

Open all three and skim. The skill **name** (frontmatter `name:` and the directory name) must match exactly.

Open `SKILL.md`. Each TODO is tagged with an anchor name. For each one: read the teaching note below, look at the placeholder in the file, then paste from [suggested-changes.md](suggested-changes.md) or write your own.

### Fill the `description` TODO

The agent matches this string against the task at hand to decide whether to invoke the skill. Specific beats categorical — vague descriptions get ignored.

→ [Suggested text](suggested-changes.md#description)

### Fill the `argument-hint` TODO

`argument-hint` declares optional inputs other agents or later chapters may pass in. We won't pass any in Chapter 1, but declaring them now makes the skill an interface with a contract, not just a prompt. Later chapters call it with real outputs from image models.

→ [Suggested text](suggested-changes.md#argument-hint)

### Fill the `one-liner` TODO

This one-sentence description is for humans reading the file — a different audience from the frontmatter `description`, which is for the agent's routing logic.

→ [Suggested text](suggested-changes.md#one-liner)

### Fill the `inputs` TODO

Declaring a field in `argument-hint` isn't enough — the body must tell the agent how to use it. This section sets the priority order so the agent doesn't have to guess.

→ [Suggested text](suggested-changes.md#inputs)

### Fill the `how-to-use` TODO

The skill ships with supporting files. `template/cxr-template.md` and `references/phrase-bank.md` are already complete — the skill body just references them so the agent reads them on demand.

→ [Suggested text](suggested-changes.md#how-to-use)

### Fill the `style-rules` TODO

When the agent has options, the skill picks one and names it. These rules close the gaps that cause run-to-run drift in hedging language and sentence structure.

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
- Borrow phrasings you can find in `references/phrase-bank.md`

If it still looks like Step 1, the agent didn't pick up the skill. Check: directory name = `write-report-simple` exactly, all three files exist, and the rule line is in `<rules>`. It also helps to start a new chat session.

Now try it on a few different images. Read each report against your own clinical impression. Where does it go right? Where does it go wrong?

## Step 4 — See the numbers (~3 min)

At this point you might be wondering: I've seen how this agent performs on a few individual images, what about testing it on a larger set? Evaluating the accuracy of general purpose radiological report generation is a complex task on its own, involving careful design of reliable metrics. Learning how to compute and how to understand these metrics is beyond the scope of this workshop, however we would like to give you a general idea how it's done.

We've already run this step's agent (with and without the skill) on a 210-case evaluation set (14 cases per NIH class, stratified) and scored every report with a real radiology metrics suite (BLEU, BERTScore, RadGraph F1, RadCliQ). Results live at `eval-results/initial/` (no skill) and `eval-results/chapter1/` (with skill) at the workshop root.

> Ground truth in `eval-results/` is model-generated from NIH labels for reference scoring; it was not written by a radiologist.

`summarize-eval` ships in `.github/skills/` — it parses the eval JSONL into a metrics-by-confidence-bucket table. We ship it pre-built so this chapter stays focused on writing the report skill.

**Open a fresh chat with no agent selected** (default "Agent", not Radiology Assistant). Ask:

```
/summarize-eval, compare these two evals:
baseline: eval-results/initial
candidate: eval-results/chapter1
```

> Note that this skill contains a Python script. The agent in your chat UI will ask for your permission to run the script to which you need to agree.

You'll get a markdown table with metrics as columns and confidence buckets as rows for each, plus a delta table. Notice that scores improve across the board, and the agent's self-reported `high` confidence cases really do score better than `medium` ones — calibration is real.

> **Two ways skills get invoked.** In Step 3 the radiology agent picked up `write-report-simple` automatically because its `description` matched what you asked it to do — that's auto-by-context. Here you named the skill explicitly in your prompt with a /<skillname> syntax (`/summarize-eval compare ...`) — that's manual invocation. Both work; explicit is useful when a skill's description is ambiguous or when several skills could plausibly handle the request. Note how typing / in chat window shows a list of available skills - that is a good way to check if your skill has been registered properly.

Takeaway: a general-purpose LLM looking at pixels is not clinically reliable; a small skill restores the structure, phrasing discipline, and calibrated confidence the workflow needs.

## (Optional) Step 5 — Extra credit

**Add to the phrase bank.** Pick a finding the bank doesn't cover well and add 2–3 example phrasings (positive / possible / negative) under a new section in `references/phrase-bank.md`. Re-run on a relevant image and see whether the agent borrows your wording.

## What you should have at the end

- [ ] `.github/skills/write-report-simple/{SKILL.md, template/cxr-template.md, references/phrase-bank.md}`
- [ ] All TODOs in `SKILL.md` filled in: `description`, `argument-hint`, `one-liner`, `inputs`, `how-to-use`, `style-rules`, `output-format`
- [ ] Updated `.github/agents/radiology-assistant.agent.md` with the "use available skills" rule
- [ ] An "after" report from Step 3 you can put next to the "before" from Step 1
- [ ] Ran `summarize-eval` against shipped results and read the comparison

If you got stuck, the completed version of every file is in `chapters/chapter1-simple-agent/answer-key/`.

## What's next

In Chapter 2 you'll give the agent **eyes**. You'll wire a vision foundation model (MedImageInsight) into the agent through a custom MCP server — first zero-shot, then with a small trained adapter on top. Every finding in the report will then trace back to actual model output instead of the LLM reading pixels.
