# CXR Report Template

The required structure for every chest X-ray report this skill produces.

## Sections

Always emit exactly these four sections, in this order, with all-caps headers:

```
INDICATION:
TECHNIQUE:
FINDINGS:
IMPRESSION:
```

- **INDICATION** — one short sentence on clinical context. If none was provided, write: `Not provided.`
- **TECHNIQUE** — one sentence describing the study (view, technique). Default: `Frontal chest radiograph.` Use `Portable AP chest radiograph.` if explicitly portable.
- **FINDINGS** — Impersonal declarative sentences (no first-person, no second-person). Mention all standard structures (lungs, pleura, heart, mediastinum, bones, and any devices present) even when normal.
- **IMPRESSION** — **numbered**, prioritized by clinical significance. One concise statement per number. Hedging language (`possible`, `differential includes`, `versus`, `cannot exclude`) is permitted and expected here.

Report text must be **plain text only** — no `**bold**`, no `###` markdown headers, no backticks. The all-caps section labels above are the only headers.

## Worked example

```
INDICATION:
Routine pre-operative screening.

TECHNIQUE:
Frontal chest radiograph.

FINDINGS:
The lungs are clear.
Heart size is normal.
No pleural effusion or pneumothorax.
Mediastinal contours are unremarkable.
No acute osseous abnormality.

IMPRESSION:
1. No acute cardiopulmonary findings.
```
