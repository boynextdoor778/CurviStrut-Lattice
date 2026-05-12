# -*- coding: utf-8 -*-
"""Deprecated generic tube-solid runner.

Use one of the size-specific runners instead:
    abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_222.py
    abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_444.py
"""
from __future__ import print_function


def main():
    print('This generic runner is deprecated.')
    print('Use: abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_222.py')
    print('  or: abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_444.py')
    raise SystemExit(1)


if __name__ == '__main__':
    main()
