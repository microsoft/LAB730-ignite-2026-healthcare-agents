# Chapter 3 images

The images below are exported from MU-Glioma-Post `PatientID_0014` (CC BY 4.0). The unchanged source volumes are in [`samples/nifti/`](../../../../samples/nifti/README.md); full DICOM and per-slice PNG series are in [`samples/dcm/`](../../../../samples/dcm/) and [`samples/png/`](../../../../samples/png/).

Contents: one representative axial brain MRI slice per study, plus a sidecar JSON with the same name. See [samples/README.md](../../../../samples/README.md) for the sidecar format and regeneration command.

| File | Study | Source volume (axial `z = 122`) | Role in Chapter 3 |
|---|---|---|---|
| `SYN0417_002.png` + `SYN0417_002.json` | Post-chemoradiation baseline | `PatientID_0014` `Timepoint_1` `brain_t1c` (about 3 weeks after radiation) | The prior. Its report is in [`../reports/SYN0417_002.md`](../reports/SYN0417_002.md). The agent reads the report; it does not re-segment this image. |
| `SYN0417_003.png` + `SYN0417_003.json` | Follow-up after chemoradiation | `PatientID_0014` `Timepoint_2` `brain_t1c` (about 9 weeks after radiation) | The current study the agent reports on. Same image as the canonical case `samples/SYN0417_003.png` used in Chapters 1 and 2. |

The chart in [`../patients/SYN0417.json`](../patients/SYN0417.json) and the prior report have not been rewritten by the export. DICOM metadata deliberately follows that fictional chart; image geometry is unchanged. Narrative alignment remains pending because the drafts were written before the case was chosen and differ in these ways:

- **Location:** the real lesion is right parietal, not left frontal.
- **Prior:** the real prior shows minimal enhancement along a small cavity, not a 25 × 20 mm nodule.
- **Current:** the new finding is rim enhancement around the cavity.
- **Timing:** about 3 and 9 weeks after radiation, rather than 4 and 8.
- **Molecular markers:** MGMT is unmethylated, not methylated.