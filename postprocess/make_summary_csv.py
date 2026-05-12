# -*- coding: utf-8 -*-
"""Collect stress-strain CSV files and compute simple scalar labels.

Usage:
    python postprocess/make_summary_csv.py tube_solid_222
    python postprocess/make_summary_csv.py tube_solid_444
"""
from __future__ import print_function
import os
import sys
import glob
import csv


def get_project_root():
    if '__file__' in globals():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.getcwd()


def get_paths(branch):
    project_root = get_project_root()
    run_root = os.path.join(project_root, 'runs', branch)
    return (os.path.join(run_root, 'results', 'curves'),
            os.path.join(run_root, 'results', 'summary'))


def read_xy(path):
    rows = []
    with open(path, 'r') as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def main():
    branch = sys.argv[1] if len(sys.argv) > 1 else 'tube_solid_222'
    curve_dir, out_dir = get_paths(branch)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    out_path = os.path.join(out_dir, 'summary_labels.csv')
    files = sorted(glob.glob(os.path.join(curve_dir, '*_stress_strain.csv')))
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['case_name', 'max_stress_MPa', 'final_strain', 'final_stress_MPa'])
        for path in files:
            rows = read_xy(path)
            if not rows:
                continue
            stresses = [float(x['stress_MPa']) for x in rows]
            strains = [float(x['strain']) for x in rows]
            name = os.path.basename(path).replace('_stress_strain.csv','')
            w.writerow([name, max(stresses), strains[-1], stresses[-1]])
    print('Branch:', branch)
    print('Read curves from:', curve_dir)
    print('Wrote:', out_path)


if __name__ == '__main__':
    main()
