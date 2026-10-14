# Sample images

The agent reads images **by path**, so every chapter can use the representative current-study slice:

```
Please write a radiology report for samples/SYN0417_003.png.
```

## Study formats

The canonical case comes from **MU-Glioma-Post** (The Cancer Imaging Archive, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). Both supplied post-contrast T1-weighted MRI volumes are available in three formats:

| Directory | Contents |
|---|---|
| [nifti/](nifti/) | Original MRI volumes and reference tumor masks, unchanged, with the original patient and time-point filenames. |
| [dcm/](dcm/) | One derived DICOM MR series per study; 155 single-slice instances per series. |
| [png/](png/) | One directory per study; 155 axial PNG slices and their JSON sidecars per study. |

| Source time point | Synthetic study | Chapter 3 study date | DICOM series | PNG slices |
|---|---|---|---|---|
| `PatientID_0014/Timepoint_1` | `SYN0417_002` (prior) | 2026-08-21 | [dcm/SYN0417_002/](dcm/SYN0417_002/) | [png/SYN0417_002/](png/SYN0417_002/) |
| `PatientID_0014/Timepoint_2` | `SYN0417_003` (current) | 2026-09-18 | [dcm/SYN0417_003/](dcm/SYN0417_003/) | [png/SYN0417_003/](png/SYN0417_003/) |

Each volume is 240 × 240 × 155 voxels at 1.0 mm isotropic spacing. Slice filenames run from `{study_id}_z000` through `{study_id}_z154`; `z` is the **zero-based NIfTI slice index**, whereas DICOM `InstanceNumber` runs from 1 through 155. All slices are included, including blank slices at the volume edges. Only the supplied post-contrast T1 series is exported, not a complete multisequence examination. The reference masks remain NIfTI-only; they are not presented as MRI images or DICOM segmentations.

The [NIfTI data card](nifti/README.md) contains the required citation, original file checksums, source clinical details, and segmentation label definitions.

## DICOM metadata and geometry

- **Patient:** `PatientID=SYN0417`, `PatientName=SYNTHETIC^SYN0417`, female, `PatientAge=058Y`, following the [fictional Chapter 3 chart](../chapters/chapter3-knowledge-sources/data/patients/SYN0417.json). No birth date or clock times are invented.
- **Study:** dates, study IDs, examination descriptions, and indications come from the matching chart entry or pending order. Clinical history includes only procedures and treatments that had started by the study date; the August prior does not claim adjuvant chemotherapy had already started.
- **Derived data:** MR Image Storage, Explicit VR Little Endian, `DERIVED\SECONDARY\OTHER`, with synthetic/de-identification notices and source provenance. `ScanningSequence=RM` and `SequenceVariant=NONE` describe the derived research series, not recovered scanner settings. Unknown scanner manufacturer, acquisition type, TR, TE, and echo-train length are left empty.
- **Pixels:** floating-point NIfTI intensities are rounded to unsigned 16-bit pixels on the original intensity scale, with an error of at most 0.5 source intensity units. No per-slice normalization or rescaling is performed. Classic MR Image Storage does not include a Modality LUT module, so no `RescaleSlope`/`RescaleIntercept` extensions are needed. This is not a lossless copy of the float data; retain the original NIfTI for exact values.
- **Geometry:** voxel positions, row/column spacing, slice thickness, and direction cosines are derived from the NIfTI affine, converting RAS world coordinates to DICOM LPS. No flipping, resampling, or geometry fabrication is performed. Both co-registered studies share a frame of reference, but have distinct study, series, and per-slice SOP instance UIDs. UIDs are deterministic for the source, chart, and export recipe.

> **Known chart/image mismatch:** the existing Chapter 3 chart is a fictional draft describing a left frontal lesion, while the source MRI shows a right parietal lesion. The chart also differs in molecular markers, timing, and prior measurements. These exports use the requested chart metadata but do **not** alter the images or silently rewrite the history to hide those differences. The mismatch is recorded in DICOM `ImageComments`. All data are **not for clinical use**.

## PNG display and sidecars

- **One axial slice per PNG**, 240 × 240, 8-bit grayscale, with no overlays or resizing.
- **Radiological orientation:** the patient's right is on the image left and anterior is at the top. With these native LPS arrays, the display is `volume[:, :, z].T`.
- **Windowing:** the 0.5th and 99.5th percentiles of positive voxels in each entire volume define a fixed linear display window for all its slices. Values outside that window are clipped to black/white. DICOM carries the same window using `VOILUTFunction=LINEAR_EXACT`.
- **JSON:** every PNG has a same-stem sidecar with patient/study IDs, date, sequence, plane, `[row, column]` pixel spacing, zero-based slice index, position, display window, source checksum/citation, and corresponding DICOM SOP instance UID. The measurement tool reads physical pixel size from this sidecar.

The existing workshop paths contain copies of **slice `z = 122`**, the representative lesion level in both studies:

| Image and sidecar | Use |
|---|---|
| [SYN0417_003.png](SYN0417_003.png) + [SYN0417_003.json](SYN0417_003.json) | Current image for Chapters 1 and 2. |
| [Chapter 3 prior PNG](../chapters/chapter3-knowledge-sources/data/images/SYN0417_002.png) + [JSON](../chapters/chapter3-knowledge-sources/data/images/SYN0417_002.json) | Prior image for the retained report. |
| [Chapter 3 current PNG](../chapters/chapter3-knowledge-sources/data/images/SYN0417_003.png) + [JSON](../chapters/chapter3-knowledge-sources/data/images/SYN0417_003.json) | Same current image, at the path used by Chapter 3. |

These representative copies retain the `{patient_id}_{study_index}.png` naming expected by the patient-history skill. When passing a numbered full-series slice to that skill, supply `patient_id=SYN0417` explicitly. Additional cases for `extra/` are still to be selected.

## Regeneration

[export_studies.py](export_studies.py) validates all four original NIfTI checksums, regenerates the DICOM/PNG files and sidecars, and refreshes the representative copies. It does not modify the source volumes or the fictional chart. Its imaging dependencies are declared inline, separate from the workshop application's dependencies.

From the repository root, using the corporate-approved Python package mirror:

```powershell
uv run --index-url https://packagefeedproxy.microsoft.io/pypi/simple/ samples\export_studies.py
```

The source images are de-identified, skull-stripped research data. Do not attempt to identify the participant. See the [data card](nifti/README.md) for attribution.