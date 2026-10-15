# Sample images

The agent reads images **by path**, so the chapters refer to files in this folder, for example:

```
Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz.
```

## Brain lesion MRI

[`mri-brain-lesions/`](mri-brain-lesions/) holds de-identified post-contrast T1-weighted brain MRI volumes as gzipped NIfTI (stored with Git LFS), one folder per case and exam date.

| Path | Used in |
|---|---|
| `case-056/2017-06-13/series-0018.nii.gz` | Chapter 1; Chapter 2 Part 1, and the prior in Part 2 |
| `case-056/2018-04-14/series-0902.nii.gz` | Chapter 2 Part 2, current study |
| `case-062/2021-06-25/series-0007.nii.gz` | Chapter 3 extra credit, as `SYN0062_001` |

Chapter 3 uses copies of these files named `{patient_id}_{study_index}.nii.gz`; see [its image list](../chapters/chapter3-knowledge-sources/data/images/README.md). Patient histories in Chapter 3 are synthetic.
