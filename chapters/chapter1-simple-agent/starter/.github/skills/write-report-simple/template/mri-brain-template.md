# Brain MRI Report Template

The required structure for every brain MRI report this skill produces.

## Sections

Always emit exactly these four sections, in this order, with all-caps headers:

```
INDICATION:
TECHNIQUE:
FINDINGS:
IMPRESSION:
```

- **INDICATION** — one short sentence on clinical context. If none was provided, write: `Not provided.`
- **TECHNIQUE** — one sentence describing the image (plane, sequence, contrast). Default: `Axial MRI image of the brain.` If the sequence is known, name it — e.g. `Axial post-contrast T1-weighted image of the brain.` or `Axial T2 FLAIR image of the brain.`
- **FINDINGS** — Impersonal declarative sentences (no first-person, no second-person). Cover any lesion (location, laterality, size, signal or enhancement), surrounding signal abnormality or edema, mass effect and midline, ventricles, and extra-axial spaces — even when normal. When you only have a single image, say so once: `Evaluation is limited to the provided axial image.`
- **IMPRESSION** — **numbered**, prioritized by clinical significance. One concise statement per number. Hedging language (`possible`, `differential includes`, `versus`, `cannot exclude`) is permitted and expected here.

Report text must be **plain text only** — no `**bold**`, no `###` markdown headers, no backticks. The all-caps section labels above are the only headers.

## Laterality

Brain MRI is displayed in radiological convention: the **patient's right is on the image left**. Always state laterality from the patient's perspective (`left frontal lobe`), never from the viewer's (`image left`).

## Measurements

Only report a size in millimeters when it was supplied by a tool (the `measurements` input). Copy the numbers verbatim, in this form:

```
The enhancing lesion measures {longest} × {perpendicular} mm (longest × perpendicular, axial).
```

Without tool-supplied measurements, describe size qualitatively (`small`, `moderate`, `large`). Never estimate millimeters from the pixels.

## Worked example

```
INDICATION:
Headache.

TECHNIQUE:
Axial T2 FLAIR image of the brain.

FINDINGS:
No focal parenchymal signal abnormality.
No mass effect or midline shift.
The ventricles and sulci are normal in size and configuration.
No extra-axial collection.
Evaluation is limited to the provided axial image.

IMPRESSION:
1. No intracranial abnormality on the provided image.
```
