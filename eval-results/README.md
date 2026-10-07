# Eval results

> 🚧 **Placeholder (Ignite 2026) — eval results pending.** The brain MRI evaluation set and metric suite are being built. Nothing in this folder is a real result yet.

The chapters compare agent versions with the pre-built `/summarize-eval` skill ([`.github/skills/summarize-eval/`](../.github/skills/summarize-eval/)). Each run lives in its own result directory:

| Directory | Agent configuration | Compared in |
|---|---|---|
| `initial/` | Chapter 1 agent, no skill | Chapter 1, Step 4 (baseline) |
| `chapter1/` | Chapter 1 agent + `write-report-simple` | Chapter 1, Step 4 · Chapter 2, Step 4 (baseline) |
| `chapter2-segment/` | + MedImageParse `segment_lesions`, `write-report-segmentation` | Chapter 2, Steps 4 and 9 |
| `chapter2-measure/` | + `measure_lesions`, `write-report-measured` | Chapter 2, Step 9 |

## Files per result directory

What `summarize-eval` reads:

- `output.jsonl` — one line per case: `{"id": ..., "confidence": "low" | "medium" | "high", ...}` (the agent's self-reported confidence).
- `section_<section>_scores.csv` — per-case metric scores, keyed by a `study_id` column; every other numeric column is treated as a metric. The default section is `none` (whole report).
- `aggregated_classification_by_confidence.csv` *(optional)* — per-confidence-bucket classification metrics for lesion detection (`accuracy`, `macro_f1`, `micro_f1`, `macro_sensitivity`, `macro_specificity`, `macro_balanced_acc`), with a `confidence` and an `n` column and an `all` row.
- `run_config.json` — how the run was produced (agent, skills, MCP servers, model, prompt).

## Planned metrics

🚧 TBD. Candidates:

- **Lesion detection** — sensitivity / specificity / F1 for lesion present vs. absent.
- **Laterality** — share of reports that put the lesion on the correct side.
- **Measurement error** — absolute error of the reported diameters vs. reference measurements, in mm (lower is better).
- **Report text** — similarity to reference reports (e.g. BLEU, BERTScore).

Reference reports and measurements are for scoring only and are not for clinical use.