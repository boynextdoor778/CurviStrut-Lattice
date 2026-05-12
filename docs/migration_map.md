# Migration map from voxel branch

## Can be reused

- Curved-X geometric logic from `write_curved_x_topology.m`
- Batch job structure from `abaqus_batch_run_all.py`
- RP compression idea from `abaqus_batch_run_all_paper_rp.py`
- CSV extraction logic for force-displacement and stress-strain curves
- README workflow style

## Must be rewritten

- `GenerateVoxel.m`
- `export_mat_voxel_to_abaqus_inp.m`
- `batch_repeat222_and_export_inp.m`
- `batch_repeat444_and_export_inp.m`
- voxel top/bottom node-set detection

## New core idea

```text
old: topology -> voxel -> C3D8 INP -> Abaqus
new: topology -> centerline paths -> beam/swept-solid model -> Abaqus
```
