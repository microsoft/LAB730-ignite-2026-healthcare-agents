---
title: "Suggested Changes — Chapter 1 Skill TODOs"
---

# Suggested Changes — Chapter 1

This file contains the answer-key text for the `SKILL.md` TODOs and the agent rule, organized by anchor. For each TODO, paste the code block below or write your own variant. The anchors here match the `<!-- TODO: <anchor> -->` tags in `SKILL.md` and the links in the Chapter 1 README.

## description

Goes in the frontmatter `description:` field. The agent uses it to decide when to invoke the skill — keep it specific.

```yaml
description: Write a structured brain MRI report (Indication, Technique, Findings, Impression) using canonical neuroradiology phrasings. Invoke whenever drafting or revising a brain MRI report.
```

## argument-hint

Declares the optional inputs other agents or later chapters can pass in. Put it under `argument-hint: |` in the frontmatter.

```yaml
argument-hint: |
  - findings: optional list of findings the caller already identified (e.g. lesions reported by a segmentation tool)
  - measurements: optional per-lesion measurements from a measurement tool (e.g. longest and perpendicular diameters in mm, laterality) — reported verbatim, never estimated
  - confidence: optional explicit hint about how certain the caller is (low / medium / high)
```

## one-liner

Replaces the `<!-- TODO: one-liner -->` comment. This sentence describes the skill for human readers, not for agent routing.

```markdown
Formats a brain MRI report (Indication, Technique, Findings, Impression) using canonical neuroradiology phrasing. Does not run image models, measure lesions, or look up priors.
```

## inputs

Replaces the `<!-- TODO: inputs -->` comment. Tells the agent how to use caller-provided values and what to fall back on when none are given.

```markdown
If the caller provides `findings`, `measurements`, or `confidence`, use them to ground the prose and the emitted confidence value. Prefer explicit `confidence` > tool-provided `findings` and `measurements` > your own read of the image. `measurements` are authoritative — copy the numbers and laterality verbatim. When nothing is provided, derive findings from the image and describe lesion size qualitatively; never invent numeric measurements.
```

## how-to-use

Replaces the `<!-- TODO: how-to-use -->` comment.

```markdown
1. Follow the section structure in [`template/mri-brain-template.md`](template/mri-brain-template.md).
2. Borrow phrasings from [`references/phrase-bank.md`](references/phrase-bank.md).
3. Apply the style rules below.
4. Wrap output in `<confidence>` and `<report>` tags as shown in **Output format**.
```

## style-rules

Replaces the `<!-- TODO: style-rules -->` comment. The first bullet distinguishes Findings from Impression — a common source of structural drift. The measurement and laterality bullets close the two gaps that matter most for brain lesions: invented sizes and flipped sides.

```markdown
- **Findings** states observations; **Impression** states interpretations.
- Match hedge strength to evidence:
  - Tool-confirmed or unequivocal: state directly. `Enhancing mass in the left frontal lobe.`
  - Moderate: use `possible` or `differential includes`.
  - Low but non-zero: use `cannot exclude`.
  - Absent: omit, or state the negative if clinically relevant.
- State negatives explicitly. Group them: `No hemorrhage, hydrocephalus, or midline shift.`
- **Numbers come from tools only.** Give sizes in millimeters only when supplied in `measurements`, copied verbatim. Otherwise describe size qualitatively (`small`, `moderate`, `large`). Never estimate millimeters from the image.
- **Laterality is the patient's.** Images use radiological convention (patient's right on image left). Prefer tool-supplied laterality when given.
- Never mention tools, models, masks, or scores inside the report.
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

- `{confidence}` — `low`, `medium`, or `high`. Use the caller-supplied value if given; otherwise derive from the evidence. Emit `low` when image quality limits the read, and note the limitation in Findings.
- `{report}` — plain text, no markdown. Follow [`template/mri-brain-template.md`](template/mri-brain-template.md) for section headers and structure.
````

## agent-rule

Add this as the first bullet in the `<rules>` block of `.github/agents/radiology-assistant.agent.md`.

```markdown
- **Use available skills when present.** If a skill is registered for the task at hand (e.g. report generation, eval summarization), invoke it rather than improvising.
- For brain MRI reports use skill write-report-simple
```