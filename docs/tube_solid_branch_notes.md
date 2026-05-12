# Tube-solid branch notes

The tube-solid branch is the current stable solid-rod simulation route.

It uses centerline JSON input and creates a lightweight solid tube mesh directly in Abaqus INP format. This avoids the extremely large voxel solid model while still giving visible rod thickness and `S, Mises` stress contours.

## Separate runners

Use size-specific scripts:

```bat
abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_222.py
abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_444.py
```

The 222 runner reads:

```text
data/rep222/json/*_rep222.json
```

The 444 runner reads:

```text
data/rep444/json/*_rep444.json
```

## Output locations

All generated files are under `runs/`:

```text
runs/tube_solid_222/
runs/tube_solid_444/
```

This keeps the project root clean.

## Current safe parameters

```python
MAX_CASES = 1
RING_SEGMENTS = 8
AXIAL_STEP = 3
CONTOUR_FREQUENCY = 'LAST_INCREMENT'
```

Use `CONTOUR_FREQUENCY = 1` only when full-frame stress animation is required. For 444, final-frame contour output is strongly preferred.
