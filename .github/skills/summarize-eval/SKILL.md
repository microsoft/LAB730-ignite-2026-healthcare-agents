---
name: summarize-eval
description: Summarize a brain MRI report eval result directory (or compare two) as a Markdown table with metrics as columns and confidence bins as rows. Invoke when the user points at one or two result-dirs and asks for a summary, calibration analysis, or comparison.
---

# summarize-eval

<!-- PLACEHOLDER: the brain MRI metric suite is not final. The script reports whatever per-case metrics the result dir contains; update the metric names in eval_summary.py and the Rules below once the suite is fixed. -->

## Single result-dir

```bash
uv run python .github/skills/summarize-eval/eval_summary.py --result-dir <result-dir>
```

**Required output, in this order:**

1. The script's stdout, copied verbatim (the Markdown tables — do not edit, re-format, drop, or re-render them).
2. The analysis bullets below.

**Analysis.** One bold headline sentence, then 2–5 free-form bullets. Classification (lesion detection) leads when present.

- **Headline (bold, 1 sentence).** What's true about this run? Lead with the
  classification verdict (or the per-case metric verdict if classification is
  absent). Cite the macro-F1 / sensitivity / specificity numbers (or the
  strongest per-case metric movement) that support it. No hedging in the
  headline.
- **Bullets.** Cover, in whatever order makes the story clearest:
  - Calibration — high vs medium (and low if n ≥ 10) on macro-F1 and
    sensitivity. Well-calibrated, flat, or inverted? Cite the gap.
  - Agreement — do the per-case metrics (laterality, measurement error, report
    text) point the same direction as the classification verdict? Name the
    metric that agrees most, or call out a disagreement explicitly.
  - Caveats — any bucket with n < 10, or suspicious values
    (specificity == sensitivity, a metric that is constant across buckets).
- Write bullets as direct observations, not labeled headers ("Laterality
  dropped -0.076…" not "**Laterality:** dropped …"). Skip any bullet that has
  nothing to say. Don't write a "summary" or "overall" bullet — the headline
  does that. Don't re-hedge magnitudes already in the headline.

## Two result-dirs (comparison)

```bash
uv run python .github/skills/summarize-eval/eval_summary.py \
    --baseline <baseline-dir> --candidate <candidate-dir>
```

**Required output, in this order:**

1. The script's stdout, copied verbatim (per-dir tables + delta table — do not edit, re-format, drop, or re-render them).
2. The analysis bullets below.

**Analysis.** One bold headline sentence, then 2–5 free-form bullets. Classification (lesion detection) leads when present.

- **Headline (bold, 1 sentence).** Did candidate beat baseline? Cite the
  macro-F1 / sensitivity / specificity deltas (or the strongest per-case metric
  delta if classification is absent). No hedging in the headline.
- **Bullets.** Cover, in whatever order makes the story clearest:
  - Calibration — did the high-vs-medium gap on macro-F1 / sensitivity widen,
    narrow, or invert? Often the real story; cite both gaps.
  - Agreement — do classification deltas and per-case metric deltas point the
    same direction? Name the metric that agrees most, or call out a
    disagreement explicitly ("text similarity dropped while detection
    improved — surface form changed, findings didn't").
  - Caveats — any bucket with n < 10. Deltas under ~0.02 on small N are
    noise; say so once.
- Write bullets as direct observations, not labeled headers. Skip any bullet
  that has nothing to say. Don't write a "summary" or "overall" bullet.

## Rules

- Metrics whose header ends in **↓** are lower-is-better (e.g. measurement
  error in mm). Every other metric is higher-is-better, including every
  classification metric (accuracy, F1, sensitivity, specificity, bal-acc).
- All numbers come from the script's output. Don't recompute.
- Always include the script's stdout tables before the analysis. Never reply with bullets only.
- Markdown only. Tables + bullets. No padding, no clinical disclaimers, no recap
  of what the metrics measure.