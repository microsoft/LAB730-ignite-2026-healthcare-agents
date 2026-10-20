---
source_image: "{{inputs.image_path}}"
prior_image: {{inputs.prior_image_path or null}}
model: "{{inputs.model}}"
conventions: {{conventions}}
derivation: AI segmentation, not reviewed by a radiologist
---

# Imaging Factsheet

## Lesion inventory
- [total.lesion.count] Lesion count: {{value}} {{unit}}.
### {{lesion}}
- [{{lesion}}.bidimensional] Diameters: {{diameters_cm[0]}} x {{diameters_cm[1]}} cm; product: {{value}} {{unit}}; measurable: {{measurable}}.
- [{{lesion}}.extent] AP x TR extent: {{value.AP}} x {{value.TR}} {{unit}}.
- [{{lesion}}.volume.{{component}}] {{component}} volume: {{value}} {{unit}}.
- [{{lesion}}.centroid] Centroid RAS: {{value}} {{unit}}.
- [{{lesion}}.pattern] Pattern proxy: {{value}}.
- [{{lesion}}.necrotic_fraction] Necrotic fraction: {{value}} {{unit}}.
- [{{lesion}}.sphericity] Sphericity: {{value}} {{unit}}; {{reason when present}}.

## Relationships
- [{{pair}}.distance] {{pair}} surface gap: {{value}} {{unit}}.
- [{{pair}}.connected_by_whole_tumor] {{pair}} connected by whole tumor: {{value}}.

## Totals and edema
- [total.volume.{{component}}] {{component}} volume: {{value}} {{unit}}.
- [total.edema.components] Edema components: {{value}} {{unit}}.
- [total.edema_to_tumor_core_ratio] Edema to tumor core: {{value}} {{unit}}; {{reason when present}}.
- [total.sum_of_products] Sum of products: {{value}} {{unit}}; lesions: {{lesions}}.

## Change from prior
- [change.{{name}}] {{name}}: prior {{prior}} {{unit}}; current {{current}} {{unit}}; change {{percent_change}} {{percent_change_unit}}; {{reason when present}}.

## Limitations
- [limitation.{{name}}] {{rule}}; {{observed_value and observed_unit when present}}.

## Images
![Film grid](film-grid.png)
![Segmentation]({{mask-stem}}.film-grid.png)
![Measurements]({{mask-stem}}.measurements.png)
