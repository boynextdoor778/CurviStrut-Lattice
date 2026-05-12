# Workflow

## 1. Generate base centerline samples

Run in MATLAB:

```matlab
cd('D:/Simulation/CurviStrut-Lattice')
addpath(genpath('matlab'))
batch_generate_curved_x_centerline
```

Output:

```text
data/base/mat/
data/base/summary_centerline.csv
data/base/preview/
```

## 2. Repeat to 2x2x2 or 4x4x4

```matlab
batch_repeat222_centerline
batch_repeat444_centerline
```

Outputs:

```text
data/rep222/mat/
data/rep222/json/
data/rep444/mat/
data/rep444/json/
```

## 3. Run Abaqus tube-solid branch

Run from the project root:

```bat
abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_222.py
abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_444.py
```

222 outputs:

```text
runs/tube_solid_222/inp/
runs/tube_solid_222/work/
runs/tube_solid_222/scratch/
runs/tube_solid_222/results/curves/
runs/tube_solid_222/results/summary/
```

444 outputs:

```text
runs/tube_solid_444/inp/
runs/tube_solid_444/work/
runs/tube_solid_444/scratch/
runs/tube_solid_444/results/curves/
runs/tube_solid_444/results/summary/
```

## 4. Read results

Open the generated ODB file from the corresponding `work/<case_name>/` folder. Use:

```text
S -> Mises
```

to view the stress contour.

The curve CSV files are stored in:

```text
runs/tube_solid_222/results/curves/
runs/tube_solid_444/results/curves/
```

## 5. Optional postprocessing

```bat
python postprocess/make_summary_csv.py tube_solid_222
python postprocess/plot_curves.py tube_solid_222
python postprocess/build_ml_dataset.py tube_solid_222
```

Use `tube_solid_444` for 4x4x4 results.
