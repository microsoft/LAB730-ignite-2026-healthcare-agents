# MU-Glioma-Post sample case (PatientID_0014)

Brain MRI for the lab's canonical case: one glioblastoma patient, two post-treatment MRI time points, with the dataset's reference tumor segmentations.

## Source and license

- **Dataset:** University of Missouri Post-operative Glioma Dataset (MU-Glioma-Post), Version 1, hosted by The Cancer Imaging Archive (TCIA).
- **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Redistribution is permitted with attribution.
- **Required data citation:**

  > Yaseen, D., Garrett, F., Gass, J., Greaser, J., Isufi, E., Layfield, L. J., Nada, A., Porgorzelski, K., Sinclair, J., Tahon, N. H. M., & Thacker, J. (2025). *University of Missouri Post-operative Glioma Dataset (MU-Glioma-Post)* (Version 1) [Data set]. The Cancer Imaging Archive. https://doi.org/10.7937/7K9K-3C83

- **Repository citation (requested by TCIA):**

  > Clark, K., Vendt, B., Smith, K., et al. (2013). The Cancer Imaging Archive (TCIA): Maintaining and Operating a Public Information Repository. *Journal of Digital Imaging*, 26(6), 1045–1057. https://doi.org/10.1007/s10278-013-9622-7

- **Changes:** none. The files below are byte-for-byte copies of the published files, with their original names.

TCIA distributes this collection only through IBM Aspera. These files were downloaded from the public Hugging Face mirror [`sbandred/mu-glioma-post-raw`](https://huggingface.co/datasets/sbandred/mu-glioma-post-raw). Their byte sizes match TCIA's own package listing exactly. The SHA-256 hashes below match the mirror's LFS object IDs.

The images are skull-stripped, de-identified research data. Don't attempt to identify the participant. Not for clinical use.

## Files

All volumes are NIfTI (`.nii.gz`), 240 × 240 × 155 voxels, 1.0 mm isotropic, co-registered to the SRI24 atlas. The arrays are stored in LPS orientation.

| File | Bytes | SHA-256 |
|---|---|---|
| `Timepoint_1/PatientID_0014_Timepoint_1_brain_t1c.nii.gz` | 5,057,361 | `96ea3e50e72693cf28fe8f1b70355ca0ed3e112fa5fb14842f005de5533e6e1f` |
| `Timepoint_1/PatientID_0014_Timepoint_1_tumorMask.nii.gz` | 27,980 | `5e822bcb9d74229df270f0bb8cd070feec03cb26747873d1eaec7278ac343a04` |
| `Timepoint_2/PatientID_0014_Timepoint_2_brain_t1c.nii.gz` | 5,157,544 | `4c60fc04ac6904a09816a03d31ab54ca42f2facf110427a9bd87c614e547fc4b` |
| `Timepoint_2/PatientID_0014_Timepoint_2_tumorMask.nii.gz` | 20,908 | `5eb101e2609aace0f305b9fc2dcf07fd647a5b8bc83c8a4ef8dc9c0257d7cea9` |

- `brain_t1c` is the skull-stripped post-contrast T1-weighted series, the "T1-Gd" sequence in the lab's prompt sets.
- `tumorMask` is the dataset's reference segmentation: automatic nnU-Net output that neuroradiologists validated and refined. Labels:
  - 1: non-enhancing tumor core
  - 2: surrounding FLAIR hyperintensity (edema or infiltrative tumor)
  - 3: enhancing tissue
  - 4: resection cavity

  The lab never shows it to the agent. It is kept as ground truth for checking MedImageParse output later.
- The same time points also have pre-contrast T1 (`brain_t1n`), FLAIR (`brain_t2f`) and T2 (`brain_t2w`) series, under the same paths in the dataset.

## The case

The clinical facts below come from TCIA's `MU-Glioma-Post_ClinicalData-July2025.xlsx`. The dataset reports days relative to diagnosis, not calendar dates.

- **Patient:** female, 53 at diagnosis. Glioblastoma, IDH1 wild-type, MGMT promoter unmethylated.
- **Treatment:** resection (day −2). Radiation 60 Gy in 30 fractions with concurrent temozolomide, days 19–61. Adjuvant temozolomide from day 113.
- **Timepoint_1, day 84 (23 days after radiation):** small right parietal resection cavity with minimal enhancement and extensive surrounding FLAIR hyperintensity. Reference volumes: enhancing 116 mm³, cavity 848 mm³, FLAIR 85,840 mm³.
- **Timepoint_2, day 126 (65 days, about 9 weeks, after radiation):** new thick rim enhancement surrounding the cavity; surrounding FLAIR hyperintensity much reduced. Reference volumes: enhancing 3,519 mm³, cavity 1,327 mm³, FLAIR 7,095 mm³. This falls inside the roughly 12-week window where treatment effect (pseudoprogression) and tumor progression look alike.
- **Afterwards:** standard therapy continued. The first documented progression came more than a year after diagnosis (day 442 in the clinical sheet).

For the lab narrative, the case has exactly the right shape: new enhancement at the operative site, weeks after chemoradiation, that the pixels alone can't classify.

## How the lab uses it

| Dataset file | Lab role |
|---|---|
| `Timepoint_2` `brain_t1c` | Canonical current study, `SYN0417_003` (Chapters 1–3) |
| `Timepoint_1` `brain_t1c` | Prior study, `SYN0417_002` (Chapter 3) |

- **Representative slice:** axial index `z = 122`, 0-based along the superior axis. It has the largest enhancing area on Timepoint_2, and because both time points are co-registered, the same index shows the same level on Timepoint_1.
- **Display:** with the native LPS array, `volume[:, :, 122].T` is already in radiological display convention (patient's right on the image left, anterior at the top).

The chart for `SYN0417` in Chapter 3 is fictional. Only the images come from this case.
