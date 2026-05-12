# CurviStrut-Lattice

![MATLAB](https://img.shields.io/badge/MATLAB-centerline%20generation-orange)
![Abaqus](https://img.shields.io/badge/Abaqus-tube--solid%20FEM-blue)
![Python](https://img.shields.io/badge/Python-batch%20automation-green)
![Status](https://img.shields.io/badge/status-final%20tube--solid%20baseline-success)

A fast **centerline-to-tube-solid Abaqus automation pipeline** for curved-strut lattice structures.  
This version replaces the previous voxel-based 4x4x4 FEM workflow with a lighter tube-solid route while keeping solid-strut stress contours and mechanical response curves.

---

## Final Stable Version

**Main workflow:** `tube_solid_branch`

```text
centerline geometry
→ repeated lattice geometry
→ tube-solid Abaqus INP
→ Abaqus compression simulation
→ S, Mises stress contour + response curves
```

The old voxel branch is kept only as a legacy/reference route. The beam branch is kept as a fast backup route. The tube-solid branch is the final main workflow.

---

## Quick Start

### 1. Generate base centerline samples

Run in MATLAB:

```matlab
batch_generate_curved_x_centerline
```

Outputs:

```text
data/base/mat/
data/base/summary_centerline.csv
```

### 2. Generate repeated lattice geometry

For **2x2x2**:

```matlab
batch_repeat222_centerline
```

For **4x4x4**:

```matlab
batch_repeat444_centerline
```

Outputs:

```text
data/rep222/mat/
data/rep222/json/
data/rep444/mat/
data/rep444/json/
```

### 3. Run Abaqus tube-solid simulation

For **2x2x2**:

```bat
abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_222.py
```

For **4x4x4**:

```bat
abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_444.py
```

### 4. Check results

For **2x2x2**:

```text
runs/tube_solid_222/results/
```

For **4x4x4**:

```text
runs/tube_solid_444/results/
```

---

## Project Structure

```text
CurviStrut-Lattice/
│
├─ matlab/
│  ├─ 01_generate_centerline/
│  ├─ 02_repeat_lattice/
│  └─ 03_export_geometry/
│
├─ abaqus/
│  ├─ common/
│  ├─ tube_solid_branch/
│  ├─ beam_branch/
│  └─ swept_solid_branch/
│
├─ data/
│  ├─ base/
│  ├─ rep222/
│  └─ rep444/
│
├─ runs/
│  ├─ tube_solid_222/
│  └─ tube_solid_444/
│
├─ postprocess/
├─ docs/
├─ legacy_voxel_reference/
└─ README.md
```

---

## Main Scripts

| Script | Purpose |
|---|---|
| `batch_generate_curved_x_centerline.m` | Generates random curved-X centerline samples. |
| `batch_repeat222_centerline.m` | Repeats base centerline samples into 2x2x2 specimens. |
| `batch_repeat444_centerline.m` | Repeats base centerline samples into 4x4x4 specimens. |
| `abaqus_batch_run_tube_solid_222.py` | Runs Abaqus tube-solid simulation for 2x2x2 specimens. |
| `abaqus_batch_run_tube_solid_444.py` | Runs Abaqus tube-solid simulation for 4x4x4 specimens. |

---

## Tube-Solid Outputs

Each successful Abaqus run generates:

```text
S, Mises stress contour in ODB
Force_Displacement CSV
Stress_Strain CSV
all_response CSV
batch_status CSV
```

Typical output folders:

```text
runs/tube_solid_222/inp/
runs/tube_solid_222/work/
runs/tube_solid_222/results/curves/
runs/tube_solid_222/results/summary/

runs/tube_solid_444/inp/
runs/tube_solid_444/work/
runs/tube_solid_444/results/curves/
runs/tube_solid_444/results/summary/
```

---

## Recommended Usage

```text
2x2x2: quick testing, debugging, and visualization.
4x4x4: final representative stress contour and response-curve results.
```

Recommended first test:

```text
MAX_CASES = 1
RING_SEGMENTS = 8
AXIAL_STEP = 3
CONTOUR_FREQUENCY = 'LAST_INCREMENT'
```

Set `MAX_CASES = None` only after confirming the workflow is stable.

---

## Legacy Notes

The previous voxel workflow is preserved in `legacy_voxel_reference/`. It is no longer the main route because the 4x4x4 voxel FEM model is computationally heavy. The current tube-solid branch is the final baseline because it runs much faster while still producing solid-strut stress contours and curve outputs.

---

## License

This project is released under the MIT License.
