# Sample images

The agent reads images **by path**, so every chapter refers to files in this folder, for example:

```
Please write a radiology report for samples/SYN0417_003.png.
```

## Source MRI

The canonical case comes from **MU-Glioma-Post** (The Cancer Imaging Archive, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). It is a glioblastoma patient with two post-treatment MRIs:

- A prior about 3 weeks after chemoradiation, showing a small resection cavity with minimal enhancement.
- A follow-up about 9 weeks after chemoradiation, showing new rim enhancement around the cavity.

The source volumes and the dataset's reference segmentations live in [`mu-glioma-post/`](mu-glioma-post/). The data card, [mu-glioma-post/README.md](mu-glioma-post/README.md), has the required citation, file checksums, and case details.

| Source volume | Lab file |
|---|---|
| `mu-glioma-post/PatientID_0014/Timepoint_2/…_brain_t1c.nii.gz` | `SYN0417_003.png` (current study) |
| `mu-glioma-post/PatientID_0014/Timepoint_1/…_brain_t1c.nii.gz` | `chapters/chapter3-knowledge-sources/data/images/SYN0417_002.png` (prior) |

> 🚧 **Placeholder — PNG slices pending.** The axial PNG slices and sidecar JSON files the lab reads haven't been exported from the volumes yet. The recommended slice is `z = 122` for both time points; see the data card. Additional cases for `extra/` are still to be selected.

## Planned contents

| Path | What it is |
|---|---|
| `SYN0417_003.png` + `SYN0417_003.json` | The canonical case used in Chapters 1 and 2: one axial post-contrast T1-weighted slice through the enhancing lesion. Same image as the current study in Chapter 3. |
| `extra/*.png` + `extra/*.json` | Additional cases (lesion and no-lesion, a mix of sequences) to swap in and see how output varies. |
| `mu-glioma-post/` | Source NIfTI volumes and reference masks the PNG slices are exported from. |

## Image format

- **PNG, one axial slice per file**, windowed for display. MedImageParse (2D) takes single images; the MCP server pads and resizes them to the 1024×1024 input the model expects.
- **Radiological orientation**: the patient's right is on the image left. The measurement tool relies on this to report laterality.
- **Naming**: `{patient_id}_{study_index}.png`. Chapter 3's `lookup-patient-history` skill infers the patient ID from this.

## Sidecar JSON

Each image ships with a sidecar of the same name (`.json` instead of `.png`). Pixels don't carry physical size, so the measurement tool reads it from here:

```json
{
  "sequence": "T1-Gd",
  "plane": "axial",
  "pixel_spacing_mm": [1.0, 1.0],
  "study_date": "2026-09-18",
  "source": "MU-Glioma-Post PatientID_0014 Timepoint_2, axial z=122 (CC BY 4.0, https://doi.org/10.7937/7K9K-3C83)"
}
```

- `sequence` — `T1-Gd` (post-contrast T1-weighted) or `FLAIR`; the segmentation skills pick their prompt set from it.
- `pixel_spacing_mm` — `[row, column]` spacing of the PNG as shipped (after any resampling), in millimeters. The MU-Glioma-Post volumes are 1.0 mm isotropic.

## Data sources

- **MU-Glioma-Post** — de-identified, skull-stripped research MRI, CC BY 4.0. Citation and details: [mu-glioma-post/README.md](mu-glioma-post/README.md).

Any patient history wrapped around an image (Chapter 3) is synthetic.