# MRI brain lesion: segmentation views and labels

MedImageParse3D fine-tuned for brain tumor components on post-contrast T1 MRI. Deployment: `MIP_DEPLOYMENT_MRI_BRAIN_LESION`.

| View | Label | Definition | Prompt |
|---|---|---|---|
| `tumor-components` | Enhancing tumor (ET) | Contrast-enhancing tumor tissue. | `post-contrast T1 MRI brain showing enhancing tumor` |
| `tumor-components` | Edema (ED) | Peritumoral edema outside the tumor core. | `post-contrast T1 MRI brain showing peritumoral edema` |
| `tumor-components` | Necrotic/non-enhancing core (NCR) | Necrotic tissue and non-enhancing tumor within the core. | `post-contrast T1 MRI brain showing necrotic/non-enhancing tumor core` |
| `whole-tumor` | Whole tumor (WT) | Union of NCR, ET, and ED. | `post-contrast T1 MRI brain showing whole tumor` |
| `tumor-core` | Tumor core (TC) | Union of NCR and ET; excludes ED. | `post-contrast T1 MRI brain showing tumor core` |

**Groups:** `[(tumor-components:*), (whole-tumor:*), (tumor-core:*)]`

`view:*` means all labels in that view. Labels within a view are mutually exclusive and can be requested together, including any subset. Request different views separately: their labels may overlap and cannot all be represented by one class per voxel.

Tumor Components is a three-class view; Whole Tumor and Tumor Core are single-label views.
