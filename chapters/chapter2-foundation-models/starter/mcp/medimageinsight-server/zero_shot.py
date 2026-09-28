# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Zero-shot CLIP-style classification on MedImageInsight embeddings.

Splits the math out of the thin endpoint client. ``mi2_client`` stays a
plain wrapper around ``/score``; this module owns text-embedding fetch,
logit scaling, softmax conversion, and the bundled label catalog used to
discover example labels.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np

from workshop import mi2_client


def classify(
    file_path: str,
    labels: list[str],
    **preprocess_kwargs,
) -> dict[str, float]:
    """Classify a medical image against text labels using MedImageInsight.
    Returns a softmax probability per label (scores sum to ~1, so labels
    compete — supply a mutually-exclusive label set).

    Labels follow ``"<modality> <body_part> <view> <condition>"`` format —
    e.g. ``"x-ray chest anteroposterior Pneumonia"``. Use
    ``label_examples()`` (or the ``zeroshot_label_examples`` MCP tool) to
    discover valid modality / body_part / view values.

    **Anti-patterns — avoid these label styles:**

    - ``"COVID-19"`` — too vague, less discriminative.
    - ``"chest X-ray showing COVID-19 pneumonia"`` — free-form prose skews
      probabilities vs. the structured format.

    **Tip:** Combine labels across modalities / body-parts / conditions in a
    single call to answer multiple questions at once. The top-scoring label
    tells you modality, anatomy, and condition together. E.g.::

        ["x-ray chest anteroposterior Pneumonia",
         "x-ray chest anteroposterior No Finding",
         "computed tomography chest axial Pneumonia",
         "magnetic resonance imaging brain sagittal normal"]

    Args:
        file_path: Path to the image file (PNG or JPEG).
        labels: Text labels to classify against, in the format above.
        **preprocess_kwargs: Passed to ``mi2_client.preprocess_image()``. (See below.)

    Preprocessing kwargs are passed to ``mi2_client.preprocess_image()``:
        image_format: Output format after preprocessing.
        jpeg_quality: JPEG quality when ``image_format`` is ``JPEG``.
        resize_to: Square resize target in pixels.
        normalize_percentiles: ``(lo, hi)`` percentile clip + rescale to 0-255,
            or ``None`` to skip normalization.
        passthrough_if_jpeg: If True and the file is already a JPEG, send the
            raw bytes unchanged (skip resize/normalize/re-encode). Use when
            inputs are already preprocessed at the target resolution.

    Returns:
        ``{label: probability}`` for each input label.
    """
    with open(file_path, "rb") as f:
        image_bytes = f.read()

    b64 = mi2_client.preprocess_image(image_bytes, **preprocess_kwargs)
    img_result = mi2_client._score([[b64, None]])
    img_feats = np.squeeze(np.array(img_result[0]["image_features"]))

    text_result = mi2_client._score([[None, label] for label in labels])
    text_feats = np.stack(
        [np.squeeze(np.array(row["text_features"])) for row in text_result]
    )
    scaling = np.exp(float(text_result[0]["scaling_factor"]))
    logits = scaling * (img_feats @ text_feats.T)

    e = np.exp(logits - logits.max())
    probs = e / e.sum()
    return dict(zip(labels, probs.tolist()))


def label_examples(
    group: str | None = None,
    regex: str | None = None,
) -> list[str]:
    """Look up built-in MedImageInsight label examples for use with
    ``zeroshot_classify`` / ``classify``.

    Use **one** of the two parameters per call:

    ``group``
        Return the unique values for a grouping column.
        Valid groups: ``modality``, ``body_part``, ``view``.

        Examples:

        - ``group="modality"``  → ``["x-ray", "ct", "mr", ...]``
        - ``group="body_part"`` → ``["abdomen", "brain", "chest", ...]``
        - ``group="view"``      → ``["anteroposterior", "axial", ...]``

    ``regex``
        Return label text strings whose text matches a regex
        (case-insensitive, Python ``re.search``).

        Examples:

        - ``regex="x-ray.*chest"`` — all chest X-ray labels
        - ``regex="pneumonia|effusion|atelectasis"`` — specific conditions
        - ``regex="pediatric.*hand"`` — bone-age labels

    Args:
        group: Return unique values for this column (mutually exclusive
            with *regex*).
        regex: Return label texts matching this pattern (mutually exclusive
            with *group*).

    Returns:
        A list of strings — either unique group values or matching label texts.
    """
    if group and regex:
        raise ValueError("Specify group or regex, not both.")
    if not group and not regex:
        raise ValueError("Specify either group or regex.")

    valid_groups = ("modality", "body_part", "view")
    csv_path = Path(__file__).with_name("label_examples.csv")
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if group:
        if group not in valid_groups:
            raise ValueError(
                f"Invalid group {group!r}. Must be one of: {', '.join(valid_groups)}"
            )
        return sorted({row[group] for row in rows if row[group]})
    compiled = re.compile(regex, re.IGNORECASE)
    return [row["text"] for row in rows if compiled.search(row["text"])]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MI2 zero-shot classification (standalone, bypasses MCP)."
    )
    parser.add_argument(
        "image",
        help="path to a chest X-ray image (e.g., samples/00026132_011.png)",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=[
            "x-ray chest anteroposterior Atelectasis",
            "x-ray chest anteroposterior Cardiomegaly",
            "x-ray chest anteroposterior Consolidation",
            "x-ray chest anteroposterior Edema",
            "x-ray chest anteroposterior Effusion",
            "x-ray chest anteroposterior Emphysema",
            "x-ray chest anteroposterior Fibrosis",
            "x-ray chest anteroposterior Hernia",
            "x-ray chest anteroposterior Infiltration",
            "x-ray chest anteroposterior Mass",
            "x-ray chest anteroposterior Nodule",
            "x-ray chest anteroposterior Pleural_Thickening",
            "x-ray chest anteroposterior Pneumonia",
            "x-ray chest anteroposterior Pneumothorax",
        ],
        help="labels to score against (default: the NIH ChestX-ray14 set)",
    )
    args = parser.parse_args()

    scores = classify(args.image, args.labels)
    for label, score in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"{label} {score:.3f}")