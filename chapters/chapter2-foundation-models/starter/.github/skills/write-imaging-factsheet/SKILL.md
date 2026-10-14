---
name: write-imaging-factsheet
description: Generate a lesion-only imaging factsheet from a post-contrast T1 MRI, optionally comparing a prior image. Use when asked for a lesion factsheet or a descriptor-based imaging summary.
argument-hint: image_path [prior_image_path]
---

# Write Imaging Factsheet

1. For each image (current and prior, if supplied), call `list_models`, then `segment` with model `mip3d-mri-brain-lesion` and its `tumor-components.prompts` verbatim, in order.
2. Call `clean_segmentation` on each returned `mask_path`. Keep the original masks, clean masks, lesion-instance masks, and sidecars.
3. Call `describe_lesions` with the current `clean_path`, passing `prior_clean_path` when available. Keep all descriptor JSON files.
4. Fill [template/factsheet.md](template/factsheet.md) from the returned descriptors only. Replace ID placeholders with actual IDs; repeat lesion, pair, total, change, and active-limitation lines as needed. Copy numbers, units, categories, booleans, and reasons verbatim. Cite descriptor IDs in brackets on every fact line. Copy frontmatter from `inputs` and `conventions`; use null for a missing prior. Omit sections with no descriptors. For unavailable values, copy null and the reason; never invent a value. Do not compute, round, diagnose, assign anatomy or side, or imply lesion matching. Save `<mask-stem>.factsheet.md` beside `<mask-stem>.descriptors.json` (replace `.descriptors.json` with `.factsheet.md`). Reply with the factsheet and paths to every artifact, including both images when comparing a prior.