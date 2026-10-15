---
name: write-report-measured
description: Write a brain MRI report with tool-computed lesion measurements and, when a prior image is supplied, change from that prior. Use for brain MRI reports when the medimageparse `segment`, `clean_segmentation`, and `describe_lesions` tools are available; preferred over write-report-segmentation.
argument-hint: image_path [prior_image_path]
---

# Write Measured Report

Build a descriptor factsheet, then let `write-report-simple` write the report from it.

1. Invoke `write-imaging-factsheet` with the image and any prior image. Keep its factsheet and each scan's `audit_dir`.
2. Invoke `write-report-simple` with:
   - `findings`: each tumor component `present` when its total volume in the factsheet is above 0, otherwise `absent`.
   - `measurements`, copied verbatim with units from the factsheet: lesion count; each lesion's diameters and tumor-core volume; total edema volume; and, with a prior, each change line (prior, current, percent change).
   - With a prior, the prior exam as the comparison, using its date if the path shows one.
3. Return the `write-report-simple` output unchanged, then end with the factsheet path and each scan's `audit_dir`.

## Rules

- Numbers come from the factsheet only. Do not compute, round, or convert them.
- Lesion IDs are ranked separately for each scan. Do not match lesions across scans or attribute change to one lesion; change lines compare totals.
- The descriptors assign no side or anatomy. Use your own read of the image, such as the overlay film grids (patient right on screen left), only for location wording.
