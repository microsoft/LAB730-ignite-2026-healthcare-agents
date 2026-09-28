# Chapter 2 — Using foundation models with agents

**Time budget: ~40 minutes.**

> Stuck? See [docs/troubleshooting.md](../../docs/troubleshooting.md).

**Prerequisites:** Chapter 1 complete, with `.github/agents/radiology-assistant.agent.md` and the `write-report-simple` + `summarize-eval` skills under `.github/skills/` at your workspace root.

## Overview

In Chapter 1 you saw that a generic LLM, even with a carefully engineered prompt, is unreliable on real chest X-rays. The way an agent skill becomes something more than a prompt is by adding **tools**. In this chapter you give the agent *eyes* by wiring it to **MedImageInsight** — a domain-specific vision foundation model — through a small **MCP (Model Context Protocol) server**. Tools are essentially Python functions that describe what they do and what their inputs and outputs are directly in their type hints and docstrings.

This chapter has two halves. In **Part 1** you wire a zero-shot MI2 tool: plug-and-play, any text labels, raw probabilities. In **Part 2** you wire a trained adapter on top of the same model: you train it once on your data, but you get calibrated per-class operating points (positive / possible / negative) in return. By the end you'll have seen both approaches on the same image and the same eval set, and you'll understand when to reach for each.

| | Zero-shot | Adapter |
|---|---|---|
| Setup | None | Train on your data |
| Labels | Any text labels at call time | Fixed set from training |
| Output | Raw probabilities you bucket | Pre-bucketed positive/possible/negative |
| Best when | No labeled data; quick first pass | Have labels + want calibration |

**Steps:**
- Setup — copy starter files, configure `.env`. (~5 min)

**Part 1 — Zero-shot**

1. Wire the `zeroshot_classify` tool. (~6 min)
2. Skim the zero-shot skill. (~2 min)
3. Try it on a sample CXR. (~6 min)
4. Compare Chapter 1 vs Part 1 zero-shot. (~2 min)

**Part 2 — Adapter**  

5. Where the adapter came from. (~1 min)  
6. Wire the `adapter_classify` tool. (~3 min)  
7. Skim the adapter skill, note the pre-bucketed output. (~2 min)  
8. Try it on the same sample CXR. (~5 min)  
9. Compare zero-shot vs adapter. (~3 min)

**(Optional) Extra credit.**

## Setup (~5 min)

**Copy the starter files** into your workspace root:

```bash
cp -r chapters/chapter2-foundation-models/starter/. .
cp    mcp/medimageinsight-server/.env.example \
      mcp/medimageinsight-server/.env
```

That gives you the following additions at workspace root. This is a **one-time setup** — no further file copying mid-chapter:

```
.github/
  agents/radiology-assistant.agent.md      ← from Chapter 1 (you'll edit this in Part 1, Step 1)
  skills/
    write-report-zeroshot/                 ← skill ships filled in — you'll skim it
    write-report-adapter/                  ← skill ships filled in — you'll skim it in Part 2
mcp/medimageinsight-server/                ← MCP server with TWO TODOs
  server.py                                ← TODO 1 (zero-shot), TODO 2 (adapter)
  zero_shot.py                             ← zero-shot scoring (read-only)
  adapter.py                               ← adapter loader/classifier (read-only)
  label_examples.csv
  .env.example
models/                                    ← prebuilt adapter bundles you'll use in Part 2
  adapter_mlp/{weights.joblib, thresholds.json}
  adapter_svm/{weights.joblib, thresholds.json}
.vscode/
  mcp.json                                 ← server registered, ready to go
```

**Fill in your `.env`.** Open `mcp/medimageinsight-server/.env` and paste in the endpoint and API key from the proctors:

```
MI2_MODEL_ENDPOINT=<get from a proctor>
MI2_MODEL_API_KEY=<get from a proctor>
```

## Part 1 — Zero-shot

Start with the simpler half: a thin wrapper around MedImageInsight's zero-shot scoring.

### Step 1 — Wire the `zeroshot_classify` tool (~6 min)

Open `mcp/medimageinsight-server/server.py` and find the **first TODO**. The pattern is already shown above it: `zeroshot_label_examples` is a working example, a thin wrapper that delegates to a function in `zero_shot.py` and pulls its docstring through the decorator.

Replace the first TODO with:

```python
@mcp.tool(description=zero_shot.classify.__doc__)
def zeroshot_classify(file_path: str, labels: list[str]) -> dict[str, float]:
    return zero_shot.classify(file_path, labels)
```

Three things matter here:

- **Decorator.** `@mcp.tool(...)` registers the function with the server. Without it, the function is invisible to the agent.
- **Type hints.** MCP uses them to build the tool schema the agent sees. `file_path: str` and `labels: list[str]` are required.
- **`description=zero_shot.classify.__doc__`** — reuses `classify`'s docstring as the tool description, so the agent gets the label-format guidance for free.

Save and confirm the tool registers. The MCP server auto-reloads (or reload manually with `Cmd/Ctrl+Shift+P` → `MCP: Reload Servers`). Open the chat tool picker (configuration icon next to the model selector) and confirm **`zeroshot_classify`** appears under **medimageinsight** alongside `zeroshot_label_examples`. Once the `.vscode/mcp.json` is in place, VS Code launches the server and interrogates it for tools — it may take a moment.

> If the tool doesn't appear, check **Output → MCP → medimageinsight** for syntax errors.

Open `.github/agents/radiology-assistant.agent.md` (from Chapter 1) and add `medimageinsight/*` to the `tools:` list:

```yaml
tools: [execute, read, agent, browser, edit, search, web, todo, medimageinsight/*]
```

This unlocks both `zeroshot_classify` and `adapter_classify` for the agent — no further agent-file edit needed in this chapter.

### Step 2 — Skim the zero-shot skill (~2 min)

The MCP tool is wired, but the agent still needs a skill that tells it *when* to call it and *what to do with the scores*. That skill ships filled in. Open `.github/skills/write-report-zeroshot/SKILL.md` and skim:

- **Frontmatter `description`** — scopes the skill to chest X-rays specifically; this is what the agent reads when deciding to load it.
- **The two-step contract** — (a) call `mcp_medimageinsig_zeroshot_classify(file_path, labels)` and bucket the scores, (b) hand the bucketed findings + raw scores off to the `write-report-simple` skill (from Chapter 1) and return what it returns. The report itself stays clean of model attribution — that's a rule in the `write-report-simple` style guide.
- **`references/labels.md`** — the canonical CXR label set the skill passes in.

*Tool-name note:* VS Code shortens long server names in tool aliases: `medimageinsight` becomes `medimageinsig`, which is why the tool ID is `mcp_medimageinsig_zeroshot_classify` and not `mcp_medimageinsight_zeroshot_classify`.

### Step 3 — Try it (~6 min)

Switch the chat agent to **Radiology Assistant** and ask:

```
Please write a radiology report for samples/00026132_011.png.
```

VS Code will ask for permissions to run third-party code — confirm each prompt.

Watch the trace: you should see one `mcp_medimageinsig_zeroshot_classify` call, then `write-report-simple` invoked, then the final report. Every stated finding should trace back to the MI2 score table the skill bucketed. The `<report>` block should read like a radiologist's note — no probability scores, no mention of MI2.

> First-call latency: the MI2 endpoint may take 30–90s to wake up if it's been idle. Subsequent calls are fast.

> If the agent writes a report without calling MI2 first, `zeroshot_classify` may not be registered. Check the tool picker under **medimageinsight**.

> **Why this matters.** The agent file and the `write-report-simple` skill are unchanged from Chapter 1. You added a new vision capability by registering an MCP tool — no agent rewrite, no skill rewrite. That's the architectural promise of MCP: add tools, don't change the harness.

### Step 4 — Compare Chapter 1 vs Part 1 zero-shot (~2 min)

Pre-baked eval results for both chapters ship under `eval-results/`. Use the `/summarize-eval` skill from Chapter 1:

```
/summarize-eval, compare these two evals:
baseline: eval-results/chapter1
candidate: eval-results/chapter2-zeroshot
```

Report-quality rubric scores will be similar — GPT has read a lot of CXR literature, so on common findings it was already a reasonable baseline. The per-finding classification numbers are higher in Chapter 2 because findings now come from MI2 instead of the LLM reading pixels. Even where overall scores look the same, the grounding path is now model output rather than LLM inference. The same wrapper pattern works for any model you want to add.

## Part 2 — Adapter

Zero-shot is one foundation-model tool. The adapter is another: a small classifier trained on top of MI2's frozen embeddings. You spend training time once, and in return the agent gets calibrated thresholds instead of raw probabilities — positive / possible / negative buckets that already encode "this label is likely true" rather than "0.31, you decide." When you have labeled data and care about calibration, train. When you don't, zero-shot.

### Step 5 — Where the adapter came from (~1 min)

The trained model bundles (already at `models/` from the Setup cp) were produced by two notebooks in `extra-credit/notebooks/`:

- `01-compute-embeddings.ipynb` — gets MI2 image embeddings for the training set (one MI2 call per image, cached).
- `02-train-adapter.ipynb` — trains classifier heads on those embeddings (Optuna search, fits per-class operating points).

Running them is extra credit. They're noted here so you can see the full pipeline: pretrained model → frozen embeddings → small classifier head → calibrated thresholds.

### Step 6 — Wire the `adapter_classify` tool (~3 min)

Open `mcp/medimageinsight-server/server.py` and find the **second TODO**. The pattern is identical to Step 1:

```python
@mcp.tool(description=adapter.classify.__doc__)
def adapter_classify(file_path: str, head: str = "mlp") -> dict[str, str]:
    return adapter.classify(file_path, head=head)
```

Same `@mcp.tool` decorator, same type-hint discipline, same docstring-as-description trick. The only change is the module (`adapter` instead of `zero_shot`) and the return type (`dict[str, str]` because the adapter returns buckets, not floats).

Reload the server (`Cmd/Ctrl+Shift+P` → `MCP: Reload Servers`) and confirm **`adapter_classify`** now appears in the tool picker alongside `zeroshot_classify`. The agent already has `medimageinsight/*` access from Step 1 — no further agent-file edit needed.

> If `adapter_classify` doesn't appear, check **Output → MCP → medimageinsight** for an import error. The most common one is `models/` not being at workspace root — it lands there from the Setup `cp`, so confirm it's a sibling of `.github/`, not buried in a subdir.

### Step 7 — Skim the adapter skill (~2 min)

Open `.github/skills/write-report-adapter/SKILL.md`. The key teaching beat: this skill consumes a dict like `{"Effusion": "positive", "Pneumothorax": "possible", ...}` — already bucketed by the adapter using calibrated per-class thresholds — instead of raw float probabilities like the zero-shot skill. The agent doesn't apply its own threshold logic; the adapter did it during training. That's what "calibrated" means in practice.

### Step 8 — Try it (~5 min)

Same prompt as Part 1:

```
Please write a radiology report for samples/00026132_011.png.
```

The agent now has two MI2 tools available. The adapter skill's `description` field steers it toward `adapter_classify` for this kind of request. Watch the trace for `mcp_medimageinsig_adapter_classify`, see the returned positive/possible/negative dict, and watch the report use that to hedge findings appropriately.

### Step 9 — Compare zero-shot vs adapter (~3 min)

```
/summarize-eval, compare these two evals:
baseline: eval-results/chapter2-zeroshot
candidate: eval-results/chapter2-adapter
```

The adapter brings tighter per-finding calibration; numbers move where the adapter's per-class thresholds disagree with the zero-shot bucket cutoffs. The headline is the trade-off from the table at the top — not "adapter wins everything." The adapter beats on classes where calibration was most off; zero-shot may hold its own on rare labels where the adapter had little training signal.

## (Optional) Extra credit

1. **Run the training notebooks yourself.** Open in order: `extra-credit/notebooks/01-compute-embeddings.ipynb` then `02-train-adapter.ipynb`. The Optuna search (cell 4 of the second notebook) is the slow step — 5–15 min depending on your machine. New bundles land in `chapters/chapter2-foundation-models/extra-credit/models/`. To use them, `cp -r` that dir over your workspace-root `models/`, then reload the MCP server.

2. **Add custom labels for zero-shot.** Pass `extra_labels` (e.g., `"x-ray chest anteroposterior COVID-19"`) via a chat prompt. The zero-shot path takes arbitrary text labels at call time and rescales scores across the new label set — watch the probabilities for your existing labels shift down as the new label competes for mass. The adapter has no equivalent: it's fixed to its trained label set.

## What you should have at the end

- [ ] `mcp/medimageinsight-server/.env` with `MI2_MODEL_ENDPOINT` and `MI2_MODEL_API_KEY` filled in
- [ ] `zeroshot_classify` and `adapter_classify` both wired in `server.py` and visible in the tool picker
- [ ] `medimageinsight/*` in the agent's `tools:` list
- [ ] A grounded report from Part 1 Step 3 (zero-shot, every finding traces to MI2 scores)
- [ ] A grounded report from Part 2 Step 8 (adapter, with positive/possible/negative findings)
- [ ] `summarize-eval` run once for Chapter 1 vs zero-shot (Step 4), once for zero-shot vs adapter (Step 9)

If you got stuck, the completed version of every file is in `chapters/chapter2-foundation-models/answer-key/`.

## What's next

In Chapter 3 you'll give the agent **context**. A real radiology read depends on more than pixels: indication, prior studies, indwelling devices, what changed since the last film. You'll give the agent access to a synthetic patient record and watch the same image produce a different report once the agent can see the chart.
