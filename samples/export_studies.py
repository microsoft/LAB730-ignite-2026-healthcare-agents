# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "nibabel>=5.3.2,<6",
#     "numpy>=2.4.4,<3",
#     "pillow>=12.2.0,<13",
#     "pydicom>=3.0.1,<4",
# ]
# ///
"""Export both sample MR studies as DICOM series and axial PNG slices."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import nibabel as nib
import numpy as np
import pydicom
from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage
from pydicom.valuerep import format_number_as_ds

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
NIFTI = SAMPLES / "nifti" / "PatientID_0014"
CHAPTER_DATA = ROOT / "chapters" / "chapter3-knowledge-sources" / "data"
STUDIES = ((1, "SYN0417_002"), (2, "SYN0417_003"))
REPRESENTATIVE_SLICE = 122
SOURCE_HASHES = {
    "PatientID_0014_Timepoint_1_brain_t1c.nii.gz":
        "96ea3e50e72693cf28fe8f1b70355ca0ed3e112fa5fb14842f005de5533e6e1f",
    "PatientID_0014_Timepoint_1_tumorMask.nii.gz":
        "5e822bcb9d74229df270f0bb8cd070feec03cb26747873d1eaec7278ac343a04",
    "PatientID_0014_Timepoint_2_brain_t1c.nii.gz":
        "4c60fc04ac6904a09816a03d31ab54ca42f2facf110427a9bd87c614e547fc4b",
    "PatientID_0014_Timepoint_2_tumorMask.nii.gz":
        "5eb101e2609aace0f305b9fc2dcf07fd647a5b8bc83c8a4ef8dc9c0257d7cea9",
}


def make_uid(key: str) -> str:
    namespace = "https://github.com/microsoft/LAB703-ignite-2026-healthcare-agents-pr"
    return f"2.25.{uuid5(NAMESPACE_URL, f'{namespace}/samples/export-v2/{key}').int}"


def check_sources() -> None:
    for timepoint, _ in STUDIES:
        for suffix in ("brain_t1c", "tumorMask"):
            name = f"PatientID_0014_Timepoint_{timepoint}_{suffix}.nii.gz"
            path = NIFTI / f"Timepoint_{timepoint}" / name
            if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_HASHES[name]:
                raise ValueError(f"Source checksum mismatch: {path}")


def patient_history(record: dict, study: dict) -> str:
    study_date = date.fromisoformat(study["date"])
    lines = [
        record["record_note"],
        f"Indication: {study['indication']}",
        f"Diagnosis: {record['diagnosis']['primary']} {record['diagnosis']['molecular']}",
        f"Established: {record['diagnosis']['established']}",
        f"Allergies: {record['allergies']['notes']}",
    ]
    for procedure in record["procedures"]:
        if date.fromisoformat(procedure["date"]) <= study_date:
            lines.append(f"{procedure['date']}: {procedure['procedure']}. {procedure['result']}")
    for treatment in record["treatments"]:
        if date.fromisoformat(treatment["start"]) <= study_date:
            end = treatment["end"]
            if end is None or date.fromisoformat(end) > study_date:
                end = "ongoing"
            lines.append(f"{treatment['start']} to {end}: {treatment['treatment']}.")
    return "\n".join(lines)


def export_study(timepoint: int, record: dict, study: dict) -> None:
    study_id = study["study_id"]
    source = NIFTI / f"Timepoint_{timepoint}" / f"PatientID_0014_Timepoint_{timepoint}_brain_t1c.nii.gz"
    image = nib.load(source)
    volume = image.get_fdata()

    # NIfTI world coordinates are RAS; DICOM patient coordinates are LPS.
    affine_lps = np.diag([-1.0, -1.0, 1.0, 1.0]) @ image.affine
    if volume.shape != (240, 240, 155) or not np.allclose(affine_lps[:3, :3], np.eye(3)):
        raise ValueError(f"Expected the native 240 x 240 x 155, 1 mm LPS sample: {source}")
    if not np.isfinite(volume).all() or volume.min() != 0 or not 0 < volume.max() <= 65535:
        raise ValueError(f"Expected MRI intensities in [0, 65535] with zero background: {source}")

    spacing = np.linalg.norm(affine_lps[:3, :3], axis=0)
    orientation = np.concatenate(
        (affine_lps[:3, 0] / spacing[0], affine_lps[:3, 1] / spacing[1])
    )
    normal = np.cross(orientation[:3], orientation[3:])
    stored = np.rint(volume).astype("<u2")
    low, high = np.percentile(volume[volume > 0], [0.5, 99.5]).tolist()
    if high <= low:
        raise ValueError(f"Cannot determine a display window: {source}")

    chart_hash = hashlib.sha256(
        json.dumps(record, sort_keys=True).encode("utf-8")
    ).hexdigest()
    source_hash = SOURCE_HASHES[source.name]
    series_uid = make_uid(f"series:{study_id}:{source_hash}:{chart_hash}")
    study_date = date.fromisoformat(study["date"]).strftime("%Y%m%d")

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset("", {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.SpecificCharacterSet = "ISO_IR 192"
    ds.SOPClassUID = MRImageStorage
    ds.ImageType = ["DERIVED", "SECONDARY", "OTHER"]
    ds.Modality = "MR"
    ds.PatientName = f"SYNTHETIC^{record['patient_id']}"
    ds.PatientID = record["patient_id"]
    ds.PatientBirthDate = ""
    ds.PatientAge = f"{record['demographics']['age']:03d}Y"
    ds.PatientSex = record["demographics"]["sex"]
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethod = "De-identified source; fictional workshop patient and dates."
    ds.AdditionalPatientHistory = patient_history(record, study)
    ds.StudyInstanceUID = make_uid(f"study:{study_id}")
    ds.SeriesInstanceUID = series_uid
    ds.FrameOfReferenceUID = make_uid(
        f"frame:{record['patient_id']}:SRI24:{json.dumps(affine_lps.tolist())}"
    )
    ds.PositionReferenceIndicator = ""
    ds.StudyID = study_id
    ds.AccessionNumber = study_id
    ds.StudyDate = study_date
    ds.SeriesDate = study_date
    ds.AcquisitionDate = study_date
    ds.ContentDate = study_date
    ds.StudyTime = ""
    ds.SeriesTime = ""
    ds.AcquisitionTime = ""
    ds.ContentTime = ""
    ds.ReferringPhysicianName = ""
    ds.StudyDescription = study["exam"]
    ds.SeriesDescription = "T1-Gd axial - derived research MRI"
    ds.SeriesNumber = 1
    ds.AcquisitionNumber = 1
    ds.ImagesInAcquisition = volume.shape[2]
    ds.BodyPartExamined = "BRAIN"
    ds.PatientPosition = ""
    ds.Manufacturer = ""
    ds.SoftwareVersions = "Ignite sample exporter v2"
    ds.ContrastBolusAgent = "Gadolinium-based contrast"
    ds.ContrastBolusRoute = "INTRAVENOUS"
    # Required MR identifiers describe this research export, not an unknown scanner sequence.
    ds.ScanningSequence = "RM"
    ds.SequenceVariant = "NONE"
    ds.ScanOptions = ""
    ds.MRAcquisitionType = ""
    ds.RepetitionTime = ""
    ds.EchoTime = ""
    ds.EchoTrainLength = ""
    ds.DerivationDescription = (
        f"Derived from MU-Glioma-Post {source.name}; SHA-256 {source_hash}. "
        "CC BY 4.0, https://doi.org/10.7937/7K9K-3C83. "
        "Skull-stripped, SRI24-registered NIfTI; geometry unchanged. "
        "Float intensities rounded to uint16 without rescaling; error <= 0.5 source intensity units. "
        "Fictional Chapter 3 patient and dates. Original scanner parameters unavailable. "
        "Only the supplied post-contrast T1 series is included. NOT FOR CLINICAL USE."
    )
    ds.ImageComments = (
        "Synthetic chart describes left frontal disease; the unmodified source MRI "
        "shows a right parietal lesion. The chart and image anatomy are not reconciled. "
        "NOT FOR CLINICAL USE."
    )
    ds.Rows = volume.shape[1]
    ds.Columns = volume.shape[0]
    ds.ImageOrientationPatient = [format_number_as_ds(float(value)) for value in orientation]
    ds.PixelSpacing = [format_number_as_ds(float(value)) for value in spacing[[1, 0]]]
    ds.SliceThickness = format_number_as_ds(float(spacing[2]))
    ds.SpacingBetweenSlices = format_number_as_ds(float(spacing[2]))
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.PixelPaddingValue = 0
    ds.WindowCenter = format_number_as_ds((low + high) / 2)
    ds.WindowWidth = format_number_as_ds(high - low)
    ds.VOILUTFunction = "LINEAR_EXACT"
    ds.PresentationLUTShape = "IDENTITY"
    ds.BurnedInAnnotation = "NO"

    dcm_dir = SAMPLES / "dcm" / study_id
    png_dir = SAMPLES / "png" / study_id
    dcm_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    for z in range(volume.shape[2]):
        stem = f"{study_id}_z{z:03d}"
        position = (affine_lps @ [0, 0, z, 1])[:3]
        ds.SOPInstanceUID = make_uid(f"instance:{series_uid}:{z}")
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
        ds.InstanceNumber = z + 1
        ds.ImagePositionPatient = [format_number_as_ds(float(value)) for value in position]
        ds.SliceLocation = format_number_as_ds(float(np.dot(position, normal)))
        ds.PixelData = np.ascontiguousarray(stored[:, :, z].T).tobytes()
        ds["PixelData"].VR = "OW"
        ds.save_as(dcm_dir / f"{stem}.dcm", enforce_file_format=True)

        # Native LPS slices, transposed to rows/columns, are already radiological.
        pixels = np.rint(
            np.clip((volume[:, :, z].T - low) / (high - low), 0, 1) * 255
        ).astype(np.uint8)
        Image.fromarray(pixels).save(png_dir / f"{stem}.png", optimize=True)
        metadata = {
            "patient_id": record["patient_id"],
            "study_id": study_id,
            "study_date": study["date"],
            "sequence": "T1-Gd",
            "plane": "axial",
            "pixel_spacing_mm": spacing[[1, 0]].tolist(),
            "slice_index": z,
            "orientation": "radiological (patient right on image left; anterior at top)",
            "image_position_patient_mm": position.tolist(),
            "display_window": {
                "nonzero_volume_percentiles": [0.5, 99.5],
                "lower": low,
                "upper": high,
                "output_range": [0, 255],
            },
            "source": (
                f"MU-Glioma-Post PatientID_0014 Timepoint_{timepoint}, axial z={z} "
                "(CC BY 4.0, https://doi.org/10.7937/7K9K-3C83)"
            ),
            "source_nifti": source.relative_to(ROOT).as_posix(),
            "source_sha256": source_hash,
            "dicom_sop_instance_uid": str(ds.SOPInstanceUID),
            "synthetic_patient_metadata": True,
            "not_for_clinical_use": True,
        }
        (png_dir / f"{stem}.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
    print(f"{study_id}: {volume.shape[2]} DICOM instances and PNG slices ({study['date']})")


def main() -> None:
    pydicom.config.settings.writing_validation_mode = pydicom.config.RAISE
    check_sources()
    record = json.loads((CHAPTER_DATA / "patients" / "SYN0417.json").read_text(encoding="utf-8"))
    studies = {
        study["study_id"]: study
        for study in record["imaging_studies"] + record["pending_orders"]
    }
    for timepoint, study_id in STUDIES:
        export_study(timepoint, record, studies[study_id])

    for _, study_id in STUDIES:
        destinations = [CHAPTER_DATA / "images"]
        if study_id == "SYN0417_003":
            destinations.append(SAMPLES)
        for destination in destinations:
            destination.mkdir(parents=True, exist_ok=True)
            for extension in ("png", "json"):
                source = SAMPLES / "png" / study_id / f"{study_id}_z{REPRESENTATIVE_SLICE:03d}.{extension}"
                shutil.copyfile(source, destination / f"{study_id}.{extension}")
    print(f"Representative slice z={REPRESENTATIVE_SLICE} copied to the existing workshop image paths.")


if __name__ == "__main__":
    main()
