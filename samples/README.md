# Sample images

The lab uses three de-identified, post-contrast T1-weighted brain MRI volumes in NIfTI (`.nii.gz`) format under [mri-brain-lesions/](mri-brain-lesions/). The two case-056 scans are used in the main walkthrough; case-062 is for Chapter 3 extra credit.

## Images used by the lab

| Sample image | Workshop use | Chapter 3 copy |
|---|---|---|
| [case-056/2017-06-13/series-0018.nii.gz](mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz) | Chapter 1 reporting; Chapter 2 segmentation and prior for comparison. | [SYN0056_002.nii.gz](../chapters/chapter3-knowledge-sources/data/images/SYN0056_002.nii.gz) |
| [case-056/2018-04-14/series-0902.nii.gz](mri-brain-lesions/case-056/2018-04-14/series-0902.nii.gz) | Current study for Chapter 2 measured reporting and Chapter 3 context-aware reporting. | [SYN0056_006.nii.gz](../chapters/chapter3-knowledge-sources/data/images/SYN0056_006.nii.gz) |
| [case-062/2021-06-25/series-0007.nii.gz](mri-brain-lesions/case-062/2021-06-25/series-0007.nii.gz) | Chapter 3 optional extra patient. | [SYN0062_001.nii.gz](../chapters/chapter3-knowledge-sources/data/images/SYN0062_001.nii.gz) |

Chapter 3 uses copies named `{patient_id}_{study_index}.nii.gz` so that `lookup-patient-history` can find the synthetic chart from the filename. See [Chapter 3 images](../chapters/chapter3-knowledge-sources/data/images/README.md) for the mapping.

## Example prompts

The agent reads images **by path**. Give paths relative to the workspace root; do not attach images directly to chat.

For Chapter 1:

```text
Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

For Chapter 2, after wiring the measurement tools:

```text
/write-report-measured Please write a radiology report for samples/mri-brain-lesions/case-056/2018-04-14/series-0902.nii.gz, comparing with the prior samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

For Chapter 3, follow the [chapter instructions](../chapters/chapter3-knowledge-sources/README.md) to copy its data folder and use the patient-based filenames.

Educational use only, **not for clinical use**. Chapter 3 patient records are synthetic. Do not attempt to identify the patients.
