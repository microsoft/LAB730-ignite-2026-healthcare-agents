---
name: write-report-segmentation
description: Write a brain MRI report grounded in MedImageParse 3D tumor segmentation. Use for brain MRI reports when the medimageparse `segment` tool is available but `clean_segmentation` or `describe_lesions` is not.
argument-hint: image_path
---

# Write Report with Segmentation

Ground lesion presence in a segmentation mask, then let `write-report-simple` write the report.

1. Call `list_models`, then call `segment` once with the absolute image path, model `mip3d-mri-brain-lesion`, and its `tumor-components.prompts` verbatim, in order.
2. Build `findings` from the returned `labels`: one entry per prompt, `present` when `detected` is true, otherwise `absent` (for example, `enhancing tumor: present`).
3. Invoke `write-report-simple` with those `findings` and no `measurements`. The raw mask is uncleaned and can include small spurious regions, so do not report `volume_ml` or estimate sizes; describe size qualitatively. Use your own read of the image, such as the overlay film grid in `images` (patient right on screen left), only for location wording.
4. Return the `write-report-simple` output unchanged, then end with the `audit_dir` from `segment`.
