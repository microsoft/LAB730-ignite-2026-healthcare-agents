---
name: write-imaging-factsheet-ehr
description: Produce an EHR imaging factsheet with mandatory segmentation, cleanup, linear dimensions, and volumes. Use when write-report-with-ehr requests imaging evidence or when explicitly asked for this factsheet.
argument-hint: image_path [prior_image_path]
---

# Write Imaging Factsheet for EHR

Use the four `medimageparse` MCP tools; VS Code may display them as `mcp_medimageparse_<tool>`.

## Required tool sequence

Perform these calls for the supplied images in this request. Loading this skill or reading an existing audit folder is not a substitute.

1. Resolve `image_path` and any `prior_image_path` to absolute paths.
2. Call `list_models` once. Select model `mip3d-mri-brain-lesion` and its `views["tumor-components"].prompts`. Pass the full prompts verbatim, in their returned order.
3. Call `segment` for the current image with that model and those prompts. Keep its `audit_dir`, `mask_path`, and review-image paths. Call `clean_segmentation` with that returned `mask_path`, using the default cleanup parameters; keep the returned `clean_path`.
4. If a prior image was supplied, call `segment` and then `clean_segmentation` for it in the same way, with the same model, prompts, and cleanup parameters. Keep the prior paths separately; never swap them with the current paths.
5. Call `describe_lesions` once with the current `clean_path`. Also pass `prior_clean_path` when a prior was supplied; omit it otherwise. Keep `descriptors_path`, `inputs`, `conventions`, `descriptors`, and the returned review-image paths.
6. Fill [template/factsheet.md](./template/factsheet.md) from the returned current descriptors and aggregate change descriptors. Save it beside `descriptors_path`, replacing `.descriptors.json` with `.factsheet.md`. Preserve all masks, sidecars, and descriptor JSON files.

If any required tool is unavailable or fails, stop and identify the step, image, and error; tell the user to check the `medimageparse` server or the reported input problem. Do not return a success-shaped factsheet or allow the parent to emit `<report>`. Do not run the server's Python code, write scripts, compute your own measurements, or substitute an earlier run.

## Filling and checking the factsheet

- Replace placeholders with actual descriptor IDs and values. Repeat the lesion, pair, volume, change, and active-limitation lines for all applicable descriptors. Cite an ID on every fact line.
- For every current lesion, copy **both `diameters_cm` entries** from `L*.bidimensional` and both `value.AP` and `value.TR` from `L*.extent`. The bidimensional `value` and `unit` describe the product in cm2, not a linear dimension. Never use `unrounded_diameters_cm`.
- Include the enhancing, necrotic, and tumor-core volumes for every current lesion, all returned total volumes, the lesion count, and sum of products. With a prior, include every `change.*` line with its prior/current values, units, percent change, and any reason.
- Include returned diameters even when `measurable` is false. That flag is not permission to omit dimensions.
- Copy numbers, units, categories, booleans, and reasons verbatim. For explicit unavailable values, preserve `null` and the reason. Never fill a missing field with zero or infer a reason.
- A successful zero-lesion result has no per-lesion descriptors: omit those sections but keep the zero count, totals, change lines when present, and limitations. It is not a tool failure.
- Do not compute, round, convert, diagnose, assign anatomy or side, or match lesion IDs across scans. Do not copy historical report sizes into this factsheet.
- Copy frontmatter from `inputs` and `conventions`, using valid YAML quoting for paths and literal `null` for a missing prior. Prior lesion descriptors are saved at `inputs.prior_descriptors_path`; the returned lesion inventory is the current scan's, not a matched current/prior inventory.
- Link the current scan's review images by filename in the Images section. Omit its measurements-image line if no measurement image was returned for the current scan, even if an image was returned for the prior.
- Before returning, check every current lesion has its diameter pair, AP/TR pair, and component volumes, and that required totals and applicable changes are present. Repair omissions from the same descriptor result or its saved JSON, not by rerunning segmentation. If a required source field is missing, stop with an explicit error naming it.

## Handoff

- **When called by `write-report-with-ehr`:** retain the factsheet and pass its contents, saved path, `descriptors_path`, and each scan's `audit_dir` back to the parent workflow, current first. Continue to the parent's report-writing step. Do not send the factsheet as the final response or end the task with audit folders.
- **When explicitly requested on its own:** reply with the completed factsheet, then its saved path and each scan's audit-log folder, current first.
