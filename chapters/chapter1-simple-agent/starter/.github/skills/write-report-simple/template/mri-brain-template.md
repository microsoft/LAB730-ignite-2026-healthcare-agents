# Brain MRI Report Template

Use all six sections below in this order, with a blank line between sections. Keep the first four on their header lines, FINDINGS as one prose paragraph, and IMPRESSION as numbered statements, one per line.

## Layout

```text
EXAM: MRI brain without and with contrast.

INDICATION: Not provided.

COMPARISON: None.

TECHNIQUE: Axial post-contrast T1-weighted MRI of the brain.

FINDINGS:
{One prose paragraph: lesion findings first, then a brief routine survey.}

IMPRESSION:
1. {Most important finding.}
2. {Next finding, if needed.}
```

## Rules

- Adapt EXAM to the supplied examination; do not infer a full protocol from a single series. INDICATION defaults to `Not provided.` COMPARISON defaults to `None.`; otherwise use the supplied prior date or description. Change and `no new lesions` require prior evidence.
- TECHNIQUE names the available series, plane, and contrast status when known; otherwise use `MRI of the brain; sequence details not provided.` Only for a single series, add a matching limitation in FINDINGS, for example `Evaluation is limited to a single post-contrast series.`
- Start FINDINGS with lesion location and patient laterality, enhancement, size, edema, and mass effect. Follow with a brief survey of ventricles and sulci, extra-axial spaces, midline, and other assessable findings, even when normal. State when a required area cannot be assessed; do not assume normality or exclude diffusion, white matter, or blood-product abnormalities without supporting evidence.
- Use IMPRESSION for the most important interpretations, with uncertainty matched to the evidence. Do not turn FINDINGS into a list.
- Numbers come from tools only. Copy sizes and midline shift from `measurements` verbatim, with units and dimensions as supplied (for example `{a} x {b} x {c} cm`); do not round or convert. Otherwise use qualitative sizes. Never estimate numbers from images.
- Use patient laterality, preferring tool-supplied sides. In radiological display, the patient's right is on image left.
- Keep the full report at most 200 words, in plain text without markdown or code fences. Never mention tools, models, masks, or scores. The skill supplies the `<confidence>` / `<report>` wrapper.

## Worked example

Generic metastasis follow-up with a supplied prior and multisequence findings; no tool measurements are supplied.

```text
EXAM: MRI brain without and with contrast.

INDICATION: Follow-up of treated brain metastasis.

COMPARISON: Prior brain MRI.

TECHNIQUE: Multiplanar brain MRI before and after contrast administration.

FINDINGS:
A small rim-enhancing lesion is again seen in the left occipital lobe, similar in size to the prior study. Surrounding vasogenic edema is unchanged, with mild local sulcal effacement. No additional enhancing lesions have developed. Ventricular caliber is maintained, and the remaining sulci are not effaced. No extra-axial fluid collection or displacement of midline structures is present. Diffusion imaging shows no acute ischemic focus, and the major vascular flow voids are preserved.

IMPRESSION:
1. Unchanged treated left occipital metastasis with surrounding edema and mild local mass effect.
2. No interval development of enhancing lesions.
```
