---
title: "Suggested Changes — Chapter 1 Skill TODOs"
---

# Suggested Changes — Chapter 1

This file contains the answer-key text for the `SKILL.md` TODOs and the agent rule, organized by anchor. For each TODO, paste the code block below or write your own variant. The anchors here match the `<!-- TODO: <anchor> -->` tags in `SKILL.md` and the links in the Chapter 1 README.

## description

Goes in the frontmatter `description:` field. The agent uses it to decide when to invoke the skill — keep it specific.

```yaml
description: Write a structured chest X-ray report (Indication, Technique, Findings, Impression) using canonical radiologist phrasings. Invoke whenever drafting or revising a CXR report.
```

## argument-hint

Declares the optional inputs other agents or later chapters can pass in. Put it under `argument-hint: |` in the frontmatter.

```yaml
argument-hint: |
  - findings: optional list of findings the caller already identified (e.g. from another tool)
  - scores: optional classifier probabilities or confidence values per finding (e.g. from a zero-shot or adapter model in later steps)
  - confidence: optional explicit hint about how certain the caller is (low / medium / high)
```

## one-liner

Replaces the `<!-- TODO: one-liner -->` comment. This sentence describes the skill for human readers, not for agent routing.

```markdown
Formats a CXR report (Indication, Technique, Findings, Impression) using canonical radiologist phrasing. Does not run image models or look up priors.
```

## inputs

Replaces the `<!-- TODO: inputs -->` comment. Tells the agent how to use caller-provided values and what to fall back on when none are given.

```markdown
If the caller provides `findings`, `scores`, or `confidence`, use them to calibrate prose hedging and the emitted confidence value. Prefer explicit `confidence` > per-finding `scores` > tone of `findings`. When nothing is provided, derive everything from the image.
```

## how-to-use

Replaces the `<!-- TODO: how-to-use -->` comment.

```markdown
1. Follow the section structure in [`template/cxr-template.md`](template/cxr-template.md).
2. Borrow phrasings from [`references/phrase-bank.md`](references/phrase-bank.md).
3. Apply the style rules below.
4. Wrap output in `<confidence>` and `<report>` tags as shown in **Output format**.
```

## style-rules

Replaces the `<!-- TODO: style-rules -->` comment. The first bullet distinguishes Findings from Impression — a common source of structural drift.

```markdown
- **Findings** states observations; **Impression** states interpretations.
- Match hedge strength to evidence:
  - High evidence or high scores: state directly. `Right lower lobe pneumonia.`
  - Moderate: use `possible` or `differential includes`.
  - Low but non-zero: use `cannot exclude`.
  - Absent: omit, or state the negative if clinically relevant.
- State negatives explicitly. Group them: `No pleural effusion or pneumothorax.`
- No padding, filler, or clinical disclaimers.
- Present tense.
```

## output-format

Replaces the `<!-- TODO: output-format -->` comment. The tags are literal text — the agent emits them as-is, not wrapped in a code block.

````markdown
```
<confidence>{confidence}</confidence>
<report>
{report}
</report>
```

- `{confidence}` — `low`, `medium`, or `high`. Use the caller-supplied value if given; otherwise derive from image evidence. Emit `low` when image quality limits the read, and note the limitation in Findings.
- `{report}` — plain text, no markdown. Follow [`template/cxr-template.md`](template/cxr-template.md) for section headers and structure.
````

## agent-rule

Add this as the first bullet in the `<rules>` block of `.github/agents/radiology-assistant.agent.md`.

```markdown
- **Use available skills when present.** If a skill is registered for the task at hand (e.g. report generation, eval summarization), invoke it rather than improvising.
- For chest xray reports use skill write-report-simple
```
