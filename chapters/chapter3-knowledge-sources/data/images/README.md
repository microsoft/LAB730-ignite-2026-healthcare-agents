# Chapter 3 images

Post-contrast T1-weighted brain MRI volumes for the synthetic charts in [`../patients/`](../patients/). Each file is a copy of a workshop sample, named `{patient_id}_{study_index}.nii.gz` so that `lookup-patient-history` can find the chart from the file name.

| File | Role | Same scan as |
|---|---|---|
| `SYN0056_006.nii.gz` | Current study, 2018-04-14 | `samples/mri-brain-lesions/case-056/2018-04-14/series-0902.nii.gz` |
| `SYN0056_002.nii.gz` | Prior study with a full report, 2017-06-13 | `samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz` |
| `SYN0062_001.nii.gz` | Extra patient, current study, 2021-06-25 | `samples/mri-brain-lesions/case-062/2021-06-25/series-0007.nii.gz` |

Each chart's `record_note` says which parts are synthetic. Not for clinical use.
