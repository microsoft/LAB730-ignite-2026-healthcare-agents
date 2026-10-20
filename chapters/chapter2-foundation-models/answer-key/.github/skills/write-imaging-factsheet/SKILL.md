---
name: write-imaging-factsheet
description: Generate a lesion-only imaging factsheet from a post-contrast T1 MRI, optionally comparing a prior image. Use when asked for a lesion factsheet or a descriptor-based imaging summary.
argument-hint: image_path [prior_image_path]
---

# Write Imaging Factsheet

1. For each image (current and prior, if supplied), call the `medimageparse` MCP tools (VS Code may list them as `mcp_medimageparse_<tool>`): `list_models`, then `segment` with model `mip3d-mri-brain-lesion` and its `tumor-components.prompts` verbatim, in order. If the tools are not available or if the run fails, stop and tell the user to check the `medimageparse` server in the tool picker. Do not run the server's Python code, write your own segmentation or measurements, or write the factsheet with a script.
2. Call `clean_segmentation` on each returned `mask_path`. Keep the original masks, clean masks, lesion-instance masks, and sidecars.
3. Call `describe_lesions` with the current `clean_path`, passing `prior_clean_path` when available. Keep all descriptor JSON files.
4. Fill [template/factsheet.md](template/factsheet.md) from the returned descriptors only. Replace ID placeholders with actual IDs; repeat lesion, pair, total, change, and active-limitation lines as needed. Copy numbers, units, categories, booleans, and reasons verbatim. Cite descriptor IDs in brackets on every fact line. Copy frontmatter from `inputs` and `conventions`; use null for a missing prior. Omit sections with no descriptors. For unavailable values, copy null and the reason; never invent a value. Do not compute, round, diagnose, assign anatomy or side, or imply lesion matching. Save `<mask-stem>.factsheet.md` beside `<mask-stem>.descriptors.json` (replace `.descriptors.json` with `.factsheet.md`). In the Images section, link the current scan's review images by file name (they sit beside the factsheet); drop the measurements line if `describe_lesions` returned none for it. Reply with the factsheet, then end with each scan's audit-log folder (`audit_dir` from `segment`), current first; the current folder holds the factsheet and images.