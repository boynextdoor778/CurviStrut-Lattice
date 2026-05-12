# Abaqus noGUI path note

Some Abaqus/CAE noGUI environments do not define the Python variable `__file__` for the main script.
The beam batch runner now detects the script path from `sys.argv` and falls back to `PROJECT_ROOT/abaqus/beam_branch` when it is launched from the project root.

Recommended command from project root:

```bat
abaqus cae noGUI=abaqus/beam_branch/abaqus_batch_run_beam.py
```
