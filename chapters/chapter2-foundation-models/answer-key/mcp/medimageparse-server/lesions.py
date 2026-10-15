"""Saved lesion cleanup and deterministic, mask-only descriptors."""

from __future__ import annotations

from copy import deepcopy
from itertools import combinations
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import ConvexHull, cKDTree, distance
from skimage.measure import label, marching_cubes, mesh_surface_area, regionprops

import figures
from segmentation import CATALOG


RULES = {
    "min_lesion_ml": 0.1,
    "merge_distance_mm": 5.0,
    "min_edema_component_ml": 0.1,
    "connectivity": 26,
    "measurable_min_diameter_cm": 1.0,
    "sum_of_products_max_lesions": 3,
    "solid_necrotic_fraction_below": 0.05,
    "rim_necrotic_fraction_at_least": 0.20,
    "sphericity_max_voxel_size_mm": 1.5,
    "slice_spacing_limitation_above_mm": 2.0,
    "geometry_tolerance": 1e-6,
    "marching_cubes_level": 0.5,
    "rounding_decimals": {"volume": 1, "dimension": 1, "distance": 1,
                          "coordinate": 1, "ratio": 2, "product": 2,
                          "sphericity": 3, "percent_change": 1},
    "lesion_order": "TC voxel count descending; ties by canonical component label",
    "sum_of_products_order": "TC volume descending among measurable lesions",
    "totals_include_subthreshold_components": False,
    "bidimensional": (
        "RAS-canonical z slices; use only the largest 8-connected TC region "
        "on each slice (ties by canonical 2D component label), including NCR. "
        "Long axis: farthest pair of TC voxel centres, "
        "extended at each end to that pixel's rectangular boundary along the axis "
        "(one pixel total along the ray). Perpendicular: longest outer TC "
        "pixel-footprint chord perpendicular to and intersecting that segment; "
        "search projected boundary-pixel corners. Outer chords can cross "
        "concavities, but never use detached regions as endpoints. "
        "Choose maximum unrounded product; ties choose lowest slice index. "
        "This is a geometric RANO-style proxy, not clinical RANO eligibility."
    ),
    "pair_distance": "Minimum Euclidean gap between TC boundary voxel cuboids with physical spacing; voxel faces, not centres",
    "lesion_grouping": "Connected groups of 26-connected TC components with surface gap <= merge_distance_mm; transitive groups filtered by TC volume >= min_lesion_ml after merging",
    "bidimensional_connectivity": 8,
}


def _record(identifier, scope, name, value, unit=None, **extra):
    return {"id": identifier, "scope": scope, "name": name,
            "value": value, "unit": unit, **extra}


def _volume(identifier, scope, name, count, voxel_ml, **extra):
    raw = float(count * voxel_ml)
    return _record(identifier, scope, name, round(raw, 1), "mL",
                   unrounded_value=raw, voxel_count=int(count), **extra)


def _stem(path):
    return path.name.removesuffix(".gz").removesuffix(".nii")


def _beside_clean(clean_path, suffix):
    return clean_path.with_name(f"{_stem(clean_path).removesuffix('.clean')}{suffix}")


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _label_roles(metadata):
    for entry in CATALOG:
        if entry["model"] != metadata.get("model"):
            continue
        for view in entry["views"].values():
            if not isinstance(view, dict) or view.get("prompts") != metadata.get("prompts"):
                continue
            roles = view.get("roles", [])
            if len(roles) == len(view["prompts"]) == 3 and set(roles) == {"enhancing", "edema", "necrotic"}:
                return {role: index for index, role in enumerate(roles, 1)}
    raise ValueError("Mask must use a catalog lesion view with exact ordered prompts and enhancing, edema, necrotic roles")


def _canonical(mask, allowed):
    if len(mask.shape) != 3:
        raise ValueError("Expected a three-dimensional categorical mask")
    canonical = nib.as_closest_canonical(mask)
    values = np.asarray(canonical.dataobj)
    if not np.isin(values, [0, *allowed]).all():
        raise ValueError("Mask contains labels outside its catalog roles")
    affine = canonical.affine.copy()
    spatial_unit = mask.header.get_xyzt_units()[0]
    scale = {"unknown": 1.0, "mm": 1.0, "meter": 1000.0, "micron": 0.001}.get(spatial_unit)
    if scale is None:
        raise ValueError("Unsupported NIfTI spatial unit")
    affine[:3] *= scale
    spacing = nib.affines.voxel_sizes(affine)
    if not np.isfinite(affine).all() or np.any(spacing <= 0):
        raise ValueError("Mask requires finite, positive physical spacing")
    directions = affine[:3, :3] / spacing
    if not np.allclose(directions.T @ directions, np.eye(3), atol=RULES["geometry_tolerance"], rtol=0):
        raise ValueError("Sheared grids require resampling before physical measurements")
    return values.astype(np.uint8), affine, spacing, spatial_unit, directions


def _save_source_grid(values, source, path):
    canonical = nib.as_closest_canonical(source)
    inverse = nib.orientations.ornt_transform(
        nib.orientations.io_orientation(canonical.affine),
        nib.orientations.io_orientation(source.affine),
    )
    restored = nib.orientations.apply_orientation(values, inverse)
    header = source.header.copy()
    header.set_data_dtype(values.dtype)
    nib.save(source.__class__(restored, source.affine, header), path)


def _surface_points(binary, spacing, offset=0):
    boundary = binary & ~ndimage.binary_erosion(binary, np.ones((3, 3, 3)))
    return (np.argwhere(boundary) + offset) * spacing


def _surface_gap(first, second, spacing, stop_at=None):
    # KD-tree candidates need a cuboid correction: standard distances use voxel centres.
    if len(first) > len(second):
        first, second = second, first
    tree = cKDTree(second)
    _, nearest = tree.query(first)
    shortest = float(np.linalg.norm(np.maximum(np.abs(first - second[nearest]) - spacing, 0), axis=1).min())
    if stop_at is not None and shortest <= stop_at:
        return shortest
    radius = (shortest if stop_at is None else stop_at) + float(np.linalg.norm(spacing))
    for point in first:
        neighbours = tree.query_ball_point(point, radius + RULES["geometry_tolerance"])
        if neighbours:
            gap = float(np.linalg.norm(np.maximum(np.abs(second[neighbours] - point) - spacing, 0), axis=1).min())
            shortest = min(shortest, gap)
            if stop_at is not None and shortest <= stop_at:
                return shortest
    return shortest


def _lesion_components(core, spacing, merge_distance_mm):
    components = label(core, connectivity=3)
    regions = regionprops(components)
    edges, surfaces = [], {}
    for first, second in combinations(regions, 2):
        first_low, first_high = np.array(first.bbox).reshape(2, 3)
        second_low, second_high = np.array(second.bbox).reshape(2, 3)
        box_gap = np.maximum(np.maximum(first_low - second_high, second_low - first_high), 0) * spacing
        if np.linalg.norm(box_gap) > merge_distance_mm:
            continue
        for region in (first, second):
            if region.label not in surfaces:
                surfaces[region.label] = _surface_points(region.image, spacing, np.array(region.bbox[:3]))
        if _surface_gap(surfaces[first.label], surfaces[second.label], spacing, merge_distance_mm) <= merge_distance_mm:
            edges.append((first.label - 1, second.label - 1))
    rows, columns = np.array(edges, dtype=int).reshape(-1, 2).T
    graph = coo_matrix((np.ones(len(edges)), (rows, columns)), shape=(len(regions), len(regions)))
    _, groups = connected_components(graph, directed=False)
    return np.r_[0, groups + 1][components]


def clean_segmentation(mask_path: str, merge_distance_mm: float = 5.0,
                       min_lesion_ml: float = 0.1, min_edema_ml: float = 0.1) -> dict:
    """Clean a segment tumor-components mask; preserve the original and label IDs.

    Exact catalog prompts determine enhancing, edema, and necrotic roles.
    Merge TC pieces by surface gap in mm, then filter TC and edema by mL.
    Save clean and L1..Ln instance NIfTIs plus a parameter sidecar beside the
    mask. Return clean_path, lesions_path, metadata_path, and lesions ranked
    by descending TC volume. Pass clean_path to describe_lesions.
    """
    if not np.isfinite([merge_distance_mm, min_lesion_ml, min_edema_ml]).all() or min(merge_distance_mm, min_lesion_ml, min_edema_ml) < 0:
        raise ValueError("Merge distance and minimum volumes must be finite and nonnegative")
    path = Path(mask_path).resolve()
    stem = _stem(path)
    metadata = json.loads(path.with_name(f"{stem}.json").read_text(encoding="utf-8"))
    roles = _label_roles(metadata)
    source = nib.load(path)
    labels, affine, spacing, _, _ = _canonical(source, roles.values())
    voxel_ml = abs(float(np.linalg.det(affine[:3, :3]))) / 1000
    core = np.isin(labels, [roles["enhancing"], roles["necrotic"]])
    groups = _lesion_components(core, spacing, merge_distance_mm)
    counts = np.bincount(groups.ravel())
    retained = [int(index) for index in np.flatnonzero((counts[1:] > 0) & (counts[1:] * voxel_ml >= min_lesion_ml)) + 1]
    retained.sort(key=lambda index: (-counts[index], index))
    mapping = np.zeros(len(counts), dtype=np.uint32)
    mapping[retained] = np.arange(1, len(retained) + 1)
    instances = mapping[groups]
    cleaned = labels.copy()
    cleaned[core & (instances == 0)] = 0
    edema = label(labels == roles["edema"], connectivity=3)
    edema_counts = np.bincount(edema.ravel())
    cleaned[(edema > 0) & (edema_counts[edema] * voxel_ml < min_edema_ml)] = 0
    result = {
        "clean_path": str(path.with_name(f"{stem}.clean.nii.gz")),
        "lesions_path": str(path.with_name(f"{stem}.lesions.nii.gz")),
        "metadata_path": str(path.with_name(f"{stem}.clean.json")),
        "lesions": [{"lesion": f"L{rank}", "tumor_core_ml": round(float(counts[index] * voxel_ml), 1)}
                    for rank, index in enumerate(retained, 1)],
    }
    _save_source_grid(cleaned, source, result["clean_path"])
    _save_source_grid(instances, source, result["lesions_path"])
    _write_json(Path(result["metadata_path"]), {
        **metadata, **result, "mask_path": str(path), "label_roles": roles,
        "parameters": {"merge_distance_mm": float(merge_distance_mm),
                       "min_lesion_ml": float(min_lesion_ml), "min_edema_ml": float(min_edema_ml)},
    })
    return result


def _perpendicular_chord(binary, spacing, endpoints):
    # No standard region property provides the RANO-style intersecting perpendicular chord.
    direction = endpoints[1] - endpoints[0]
    direction /= np.linalg.norm(direction)
    normal = np.array([-direction[1], direction[0]])
    boundary = binary & ~ndimage.binary_erosion(binary)
    centres = np.argwhere(boundary) * spacing
    offsets = np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]]) * spacing
    corners = centres[:, None, :] + offsets
    starts = corners.reshape(-1, 2)
    ends = np.roll(corners, -1, axis=1).reshape(-1, 2)
    along_start, along_end = starts @ direction, ends @ direction
    across_start, across_end = starts @ normal, ends @ normal
    lower, upper = sorted(endpoints @ direction)
    crossing = float(endpoints[0] @ normal)
    candidates = np.unique(np.clip(along_start, lower, upper))
    delta = along_end - along_start
    tolerance = RULES["geometry_tolerance"]
    sloped = np.abs(delta) > tolerance
    best_length, best_segment = -1.0, None
    for position in candidates:
        valid = sloped & (position >= np.minimum(along_start, along_end) - tolerance) & (position <= np.maximum(along_start, along_end) + tolerance)
        fractions = np.divide(position - along_start, delta, out=np.zeros_like(delta), where=sloped)
        intersections = across_start[valid] + fractions[valid] * (across_end - across_start)[valid]
        parallel = ~sloped & (np.abs(position - along_start) <= tolerance)
        intersections = np.concatenate([intersections, across_start[parallel], across_end[parallel]])
        if not intersections.size:
            continue
        low, high = float(intersections.min()), float(intersections.max())
        if low - tolerance <= crossing <= high + tolerance and high - low > best_length:
            best_length = high - low
            best_segment = np.array([position * direction + low * normal, position * direction + high * normal])
    return best_length, best_segment


def _long_axis(binary, spacing):
    # Regionprops Feret diameter uses different boundaries than the centre-plus-pixel rule used here.
    centres = np.argwhere(binary) * spacing
    if len(centres) == 1:
        direction = np.eye(2)[int(np.argmax(spacing))]
        endpoints = np.stack([centres[0], centres[0]])
    else:
        if len(centres) > 2 and np.linalg.matrix_rank(centres - centres[0]) == 2:
            centres = centres[ConvexHull(centres).vertices]
        distances = distance.squareform(distance.pdist(centres))
        first, second = np.unravel_index(np.argmax(distances), distances.shape)
        endpoints = centres[[first, second]].copy()
        direction = endpoints[1] - endpoints[0]
        direction /= np.linalg.norm(direction)
    ray_width = float(np.min(np.divide(spacing, np.abs(direction), out=np.full(2, np.inf), where=np.abs(direction) > RULES["geometry_tolerance"])))
    endpoints[0] -= direction * ray_width / 2
    endpoints[1] += direction * ray_width / 2
    return endpoints


def _bidimensional(core, spacing):
    best = None
    for slice_index in np.flatnonzero(core.any(axis=(0, 1))):
        regions = label(core[:, :, slice_index], connectivity=2)
        counts = np.bincount(regions.ravel())
        binary = regions == (int(np.argmax(counts[1:])) + 1)
        endpoints = _long_axis(binary, spacing[:2])
        long_mm = float(np.linalg.norm(endpoints[1] - endpoints[0]))
        perpendicular_mm, perpendicular = _perpendicular_chord(binary, spacing[:2], endpoints)
        product = long_mm * perpendicular_mm / 100
        if best is None or product > best["product_cm2"]:
            segments = [np.column_stack([segment / spacing[:2], np.full(2, slice_index)]).tolist()
                        for segment in (endpoints, perpendicular)]
            best = {"diameters_cm": [long_mm / 10, perpendicular_mm / 10],
                    "product_cm2": product, "slice_index": int(slice_index),
                    "segments_canonical_voxels": segments}
    return best


def _bidimensional_record(region, spacing, affine, lesion):
    measurement = _bidimensional(region.image, spacing)
    offset = np.array(region.bbox[:3])
    measurement["slice_index"] += int(offset[2])
    segments = np.array(measurement["segments_canonical_voxels"]) + offset
    measurement["segments_canonical_voxels"] = segments.tolist()
    measurement["segments_ras_mm"] = nib.affines.apply_affine(affine, segments).tolist()
    raw_product = measurement["product_cm2"]
    measurable = min(measurement["diameters_cm"]) >= RULES["measurable_min_diameter_cm"]
    measurement["unrounded_diameters_cm"] = measurement["diameters_cm"]
    measurement["diameters_cm"] = [round(value, 1) for value in measurement["diameters_cm"]]
    measurement["product_cm2"] = round(raw_product, 2)
    measurement["unrounded_product_cm2"] = raw_product
    return _record(f"{lesion}.bidimensional", "lesion", "bidimensional", measurement["product_cm2"], "cm2", lesion=lesion,
                   **measurement, measurable=bool(measurable),
                   rule=RULES["bidimensional"] + " Measurable iff both unrounded diameters >= measurable_min_diameter_cm.")


def _sphericity_record(region, spacing, voxel_ml, lesion):
    sphericity, area, reason = None, None, None
    if spacing.max() <= RULES["sphericity_max_voxel_size_mm"]:
        vertices, faces, _, _ = marching_cubes(np.pad(region.image.astype(np.uint8), 1), level=RULES["marching_cubes_level"], spacing=spacing)
        area = float(mesh_surface_area(vertices, faces))
        sphericity = float(np.pi ** (1 / 3) * (6 * region.area * voxel_ml * 1000) ** (2 / 3) / area)
    else:
        reason = "Maximum voxel size exceeds sphericity_max_voxel_size_mm"
    return _record(f"{lesion}.sphericity", "lesion", "sphericity", None if sphericity is None else round(sphericity, 3), "ratio", lesion=lesion, surface_area_mm2=area, reason=reason,
                   rule="pi^(1/3)*(6*TC_volume_mm3)^(2/3)/marching_cubes_area_mm2; only max voxel size <= 1.5 mm")


def _lesion_records(region, labels, roles, affine, spacing, voxel_ml):
    lesion = f"L{region.label}"
    core = region.image
    local_labels = labels[region.slice]
    descriptors = []
    for name, included in (("enhancing", core & (local_labels == roles["enhancing"])),
                           ("necrotic", core & (local_labels == roles["necrotic"])), ("tumor_core", core)):
        descriptors.append(_volume(f"{lesion}.volume.{name}", "lesion", f"volume.{name}", int(included.sum()), voxel_ml, lesion=lesion))
    extent = np.array(core.shape) * spacing / 10
    descriptors.append(_record(f"{lesion}.extent", "lesion", "extent", {"AP": round(float(extent[1]), 1), "TR": round(float(extent[0]), 1)}, "cm", lesion=lesion))
    centroid = nib.affines.apply_affine(affine, region.centroid)
    descriptors.append(_record(f"{lesion}.centroid", "lesion", "centroid", np.round(centroid, 1).tolist(), "mm", lesion=lesion))
    descriptors.append(_bidimensional_record(region, spacing, affine, lesion))
    fraction = float(np.count_nonzero(core & (local_labels == roles["necrotic"])) / region.area)
    pattern = "solid" if fraction < RULES["solid_necrotic_fraction_below"] else "heterogeneous" if fraction < RULES["rim_necrotic_fraction_at_least"] else "rim"
    descriptors.append(_record(f"{lesion}.pattern", "lesion", "enhancement_pattern", pattern, lesion=lesion,
                               rule="NCR/TC < 0.05: solid; 0.05 <= NCR/TC < 0.20: heterogeneous; >= 0.20: rim. Fraction proxy only."))
    descriptors.append(_record(f"{lesion}.necrotic_fraction", "lesion", "necrotic_fraction", round(fraction, 2), "ratio", lesion=lesion, unrounded_value=fraction))
    descriptors.append(_sphericity_record(region, spacing, voxel_ml, lesion))
    return descriptors


def _pair_records(instances, labels, spacing):
    whole_components = label(labels > 0, connectivity=3)
    regions = regionprops(instances)
    whole_ids = {region.label: set(np.unique(whole_components[region.slice][region.image]).tolist()) for region in regions}
    descriptors = []
    for first, second in combinations(regions, 2):
        names = [f"L{first.label}", f"L{second.label}"]
        shortest = _surface_gap(
            _surface_points(first.image, spacing, np.array(first.bbox[:3])),
            _surface_points(second.image, spacing, np.array(second.bbox[:3])), spacing,
        )
        descriptors.append(_record(f"{'-'.join(names)}.distance", "pair", "distance", round(shortest, 1), "mm", lesions=names, rule=RULES["pair_distance"]))
        descriptors.append(_record(f"{'-'.join(names)}.connected_by_whole_tumor", "pair", "connected_by_whole_tumor", bool(whole_ids[first.label] & whole_ids[second.label]), lesions=names, rule="The TC groups share at least one 26-connected ET|ED|NCR component"))
    return descriptors


def _total_records(labels, roles, voxel_ml, lesion_records):
    core = np.isin(labels, [roles["enhancing"], roles["necrotic"]])
    edema = labels == roles["edema"]
    descriptors = []
    for name, included in (("enhancing", labels == roles["enhancing"]), ("necrotic", labels == roles["necrotic"]), ("tumor_core", core), ("edema", edema), ("whole_tumor", labels > 0)):
        descriptors.append(_volume(f"total.volume.{name}", "total", f"volume.{name}", int(included.sum()), voxel_ml))
    edema_count = int(label(edema, connectivity=3).max())
    descriptors.append(_record("total.edema.components", "total", "edema.components", edema_count, "count", rule="26-connected ED components with unrounded volume >= min_edema_component_ml"))
    ratio = float(edema.sum() / core.sum()) if core.any() else None
    descriptors.append(_record("total.edema_to_tumor_core_ratio", "total", "edema_to_tumor_core_ratio", None if ratio is None else round(ratio, 2), "ratio", reason="TC is zero" if ratio is None else None))
    used = [record for record in lesion_records if record["name"] == "bidimensional" and record["measurable"]][:RULES["sum_of_products_max_lesions"]]
    product_total = float(sum(record["unrounded_product_cm2"] for record in used))
    descriptors.append(_record("total.sum_of_products", "total", "sum_of_products", round(product_total, 2), "cm2", lesions=[record["lesion"] for record in used], unrounded_value=product_total,
                               rule="Sum unrounded products of up to 3 largest TC-volume lesions with both connected-TC diameters >= 1.0 cm"))
    return descriptors


def _limitation_records(spacing, spatial_unit, directions):
    limitations = {
        "slice_spacing": (bool(spacing[2] > RULES["slice_spacing_limitation_above_mm"]), "Canonical z spacing > 2 mm; coarse sampling limits slice selection and through-plane grouping", ["bidimensional", "lesion_grouping", "volumes"], float(spacing[2])),
        "t1_only_edema": (True, "ED inferred from post-contrast T1 only, without T2/FLAIR confirmation", ["edema", "whole_tumor"], None),
        "no_anatomical_filtering": (True, "No anatomical filtering; components outside brain are retained", ["lesions", "totals"], None),
        "no_location": (True, "No laterality or anatomical location assigned", ["location"], None),
        "unknown_spatial_units": (spatial_unit == "unknown", "Unknown NIfTI spatial units are assumed mm", ["all_physical_measurements"], None),
        "oblique_grid": (not np.allclose(directions, np.eye(3), atol=RULES["geometry_tolerance"], rtol=0), "Canonicalization permutes/flips only; oblique canonical z is not anatomical axial", ["extent", "bidimensional"], None),
        "discrete_surface_distance": (True, RULES["pair_distance"], ["pair_distance", "lesion_grouping"], None),
        "geometric_bidimensional_proxy": (True, RULES["bidimensional"], ["sum_of_products", "measurable"], None),
    }
    return [_record(f"limitation.{name}", "limitation", name, bool(active), rule=rule, affects=affects, observed_value=observed, observed_unit="mm" if observed is not None else None)
            for name, (active, rule, affects, observed) in limitations.items()]


def _change_records(result, prior):
    if prior["rules"] != result["rules"]:
        raise ValueError("Prior descriptor rules must match current rules")
    previous = {record["id"]: record for record in prior["descriptors"]}
    current = {record["id"]: record for record in result["descriptors"]}
    descriptors = []
    for name in ("volume.tumor_core", "volume.enhancing", "volume.edema", "volume.whole_tumor", "sum_of_products"):
        old, new = previous[f"total.{name}"], current[f"total.{name}"]
        old_raw, new_raw = old["unrounded_value"], new["unrounded_value"]
        if name == "sum_of_products" and previous["total.lesion.count"]["value"] != current["total.lesion.count"]["value"]:
            descriptors.append(_record("change.sum_of_products", "change", name, None, new["unit"], prior=old["value"], current=new["value"], percent_change=None, percent_change_unit="%", prior_unrounded=old_raw, current_unrounded=new_raw,
                                       reason="Current and prior lesion counts differ", prior_lesion_count=previous["total.lesion.count"]["value"], current_lesion_count=current["total.lesion.count"]["value"], rule="Compare sum of products only when lesion counts are equal; no lesion matching"))
            continue
        percent = 100 * (new_raw - old_raw) / old_raw if old_raw else None
        descriptors.append(_record(f"change.{name}", "change", name, new["value"], new["unit"], prior=old["value"], current=new["value"], percent_change=None if percent is None else round(percent, 1), percent_change_unit="%", prior_unrounded=old_raw, current_unrounded=new_raw, reason="Prior value is zero" if percent is None else None, rule="100*(current-prior)/prior using unrounded totals; null if prior=0; no lesion matching"))
    return descriptors


def _read_clean(path):
    if not path.name.endswith(".clean.nii.gz"):
        raise ValueError("Pass a .clean.nii.gz mask returned by clean_segmentation")
    metadata = json.loads(path.with_name(f"{_stem(path)}.json").read_text(encoding="utf-8"))
    roles = _label_roles(metadata)
    if roles != metadata["label_roles"]:
        raise ValueError("Clean mask roles no longer match the catalog")
    source = nib.load(path)
    geometry = _canonical(source, roles.values())
    lesion_image = nib.load(metadata["lesions_path"])
    if source.shape != lesion_image.shape or not np.allclose(source.affine, lesion_image.affine, atol=RULES["geometry_tolerance"], rtol=0):
        raise ValueError("Clean and lesion masks must share the same source grid")
    instances = np.asarray(nib.as_closest_canonical(lesion_image).dataobj)
    count = len(metadata["lesions"])
    if not np.isin(instances, np.arange(count + 1)).all() or set(np.unique(instances[instances > 0])) != set(range(1, count + 1)):
        raise ValueError("Lesion instance IDs must match the clean sidecar")
    core = np.isin(geometry[0], [roles["enhancing"], roles["necrotic"]])
    if not np.array_equal(instances > 0, core):
        raise ValueError("Lesion instances must cover exactly the cleaned tumor core")
    return metadata, roles, geometry, instances.astype(np.uint32)


def _describe_clean(path):
    metadata, roles, geometry, instances = _read_clean(path)
    labels, affine, spacing, spatial_unit, directions = geometry
    voxel_ml = abs(float(np.linalg.det(affine[:3, :3]))) / 1000
    regions = regionprops(instances)
    descriptors = [_record("total.lesion.count", "total", "count", len(regions), "count", rule=RULES["lesion_grouping"])]
    for region in regions:
        descriptors.extend(_lesion_records(region, labels, roles, affine, spacing, voxel_ml))
    descriptors.extend(_pair_records(instances, labels, spacing))
    descriptors.extend(_total_records(labels, roles, voxel_ml, descriptors))
    descriptors.extend(_limitation_records(spacing, spatial_unit, directions))
    parameters = metadata["parameters"]
    rules = deepcopy(RULES)
    rules.update(labels=roles, merge_distance_mm=parameters["merge_distance_mm"], min_lesion_ml=parameters["min_lesion_ml"], min_edema_component_ml=parameters["min_edema_ml"])
    return {
        "inputs": {**{key: metadata[key] for key in ("image_path", "model", "prompts", "mask_path")},
                   "clean_path": str(path), "lesions_path": metadata["lesions_path"],
                   "voxel_size_mm": spacing.tolist(), "slice_spacing_mm": float(spacing[2]),
                   "canonical_affine_ras_mm": affine.tolist(), "source_spatial_unit": spatial_unit},
        "conventions": {"volumes": "mL", "dimensions": "AP x TR, cm; inclusive canonical voxel bounding box", "distances": "mm, shortest 3D surface-to-surface gap between voxel cuboids", "coordinates": "RAS, mm", "slice_index": "zero-based RAS-canonical z", "rounding": "Python round, ties to even; category and change calculations use unrounded values; precision in rules", "lesion_ids": "scan-local rank only; no cross-exam matching", "schema_version": 2},
        "rules": rules, "descriptors": descriptors,
    }


def describe_lesions(clean_path: str, prior_clean_path: str | None = None) -> dict:
    """Describe saved clean and lesion-instance masks; optionally compare a prior.

    Return descriptors_path plus ID-tagged volumes, AP/TR extents, RAS
    centroids, bidimensional proxies, patterns, sphericity, relationships,
    totals, change, and limitations. Save JSON beside the masks; save prior
    descriptors too when supplied. Measurements use cleaned voxels only.
    IDs rank each scan independently. No diagnosis, anatomy, or side is inferred.
    Also save <mask stem>.measurements.png per scan with lesions, showing each
    lesion's measured slice; return those paths as images.
    """
    path = Path(clean_path).resolve()
    result = _describe_clean(path)
    images = [figures.save_measurements(result, _beside_clean(path, ".measurements.png"))]
    if prior_clean_path is not None:
        prior_path = Path(prior_clean_path).resolve()
        prior = _describe_clean(prior_path)
        result["descriptors"].extend(_change_records(result, prior))
        prior_output = _beside_clean(prior_path, ".descriptors.json")
        _write_json(prior_output, prior)
        images.append(figures.save_measurements(prior, _beside_clean(prior_path, ".measurements.png")))
        result["inputs"].update(prior_image_path=prior["inputs"]["image_path"], prior_clean_path=str(prior_path), prior_descriptors_path=str(prior_output))
    output = _beside_clean(path, ".descriptors.json")
    _write_json(output, result)
    return {"descriptors_path": str(output), "images": [image for image in images if image], **result}