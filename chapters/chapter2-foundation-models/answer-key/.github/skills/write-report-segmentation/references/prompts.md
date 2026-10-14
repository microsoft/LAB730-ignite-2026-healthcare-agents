# Brain lesion prompts (MedImageParse format)

Pass these strings as the `prompts` argument to `segment_lesions`, **verbatim**. Pick the set that matches the image's MRI sequence — the `sequence` field in the image's sidecar JSON. The first prompt in each set is the **primary target**: the one that gets measured in Chapter 2 Part 2 and compared against priors in Chapter 3.

MedImageParse is prompted with short target names, not sentences. Avoid free-form prose (`"is there a tumor in this brain?"`) — it doesn't match how the model was trained.

<!-- PLACEHOLDER: confirm the final prompt sets against the MedImageParse supported-target list and the shipped sample sequences. -->

## T1-Gd — post-contrast T1-weighted (default)

```
enhancing tumor
non-enhancing tumor
```

## FLAIR

```
edema
lower-grade glioma
```

Call the `prompt_examples` tool to browse the full catalog.
