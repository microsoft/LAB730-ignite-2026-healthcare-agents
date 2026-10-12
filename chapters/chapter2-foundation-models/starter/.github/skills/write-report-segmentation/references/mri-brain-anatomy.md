# MRI brain anatomy: segmentation labels and prompts

MedImageParse3D fine-tuned on Mindboggle-101 T1-weighted MRI for 18 anatomy classes across tissue, structure-landmark, and lobar-cortex views. Deployment: `MIP_DEPLOYMENT_MRI_BRAIN_ANATOMY`.

**Prompt template:** `T1-weighted MRI brain showing {label}`. Replace underscores in the normalized label with spaces.

| View | Label | Definition |
|---|---|---|
| `tissue` | `left_cerebral_white_matter` | White matter of the left cerebral hemisphere. |
| `tissue` | `right_cerebral_white_matter` | White matter of the right cerebral hemisphere. |
| `tissue` | `left_cortical_gray_matter` | Cortical gray matter of the left cerebral hemisphere. |
| `tissue` | `right_cortical_gray_matter` | Cortical gray matter of the right cerebral hemisphere. |
| `structure_landmarks` | `left_lateral_ventricle` | Left lateral ventricle, including its inferior horn. |
| `structure_landmarks` | `right_lateral_ventricle` | Right lateral ventricle, including its inferior horn. |
| `structure_landmarks` | `left_postcentral_gyrus` | Cortical ribbon of the left postcentral gyrus. |
| `structure_landmarks` | `left_precentral_gyrus` | Cortical ribbon of the left precentral gyrus. |
| `structure_landmarks` | `right_postcentral_gyrus` | Cortical ribbon of the right postcentral gyrus. |
| `structure_landmarks` | `right_precentral_gyrus` | Cortical ribbon of the right precentral gyrus. |
| `lobar_cortex` | `left_frontal_cortex` | Union of mapped left frontal cortical parcels. |
| `lobar_cortex` | `left_occipital_cortex` | Union of mapped left occipital cortical parcels. |
| `lobar_cortex` | `left_temporal_cortex` | Union of mapped left temporal cortical parcels. |
| `lobar_cortex` | `left_parietal_cortex` | Union of mapped left parietal cortical parcels. |
| `lobar_cortex` | `right_frontal_cortex` | Union of mapped right frontal cortical parcels. |
| `lobar_cortex` | `right_occipital_cortex` | Union of mapped right occipital cortical parcels. |
| `lobar_cortex` | `right_temporal_cortex` | Union of mapped right temporal cortical parcels. |
| `lobar_cortex` | `right_parietal_cortex` | Union of mapped right parietal cortical parcels. |

Lobar-cortex labels exclude underlying white matter. Join full prompts with `&` when requesting multiple labels.

## Overlap-safe combinations

Groups: [(tissue:*), (structure_landmarks:*), (lobar_cortex:*)].

Here, `view:*` means all labels in that view. Any subset of a group is safe to request together. Use separate calls for different views to preserve overlapping targets; the endpoint returns one class per voxel.
