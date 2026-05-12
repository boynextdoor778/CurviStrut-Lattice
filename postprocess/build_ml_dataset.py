# -*- coding: utf-8 -*-
"""Build an initial ML table by merging JSON parameters with scalar labels.

Usage:
    python postprocess/build_ml_dataset.py tube_solid_222
    python postprocess/build_ml_dataset.py tube_solid_444
"""
from __future__ import print_function
import os
import sys
import glob
import json
import csv


def get_project_root():
    if '__file__' in globals():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.getcwd()


def load_labels(path):
    d = {}
    if not os.path.isfile(path):
        return d
    with open(path, 'r') as f:
        r = csv.DictReader(f)
        for row in r:
            d[row['case_name']] = row
    return d


def main():
    branch = sys.argv[1] if len(sys.argv) > 1 else 'tube_solid_222'
    project_root = get_project_root()
    rep_name = 'rep222' if branch.endswith('222') else 'rep444'
    json_dir = os.path.join(project_root, 'data', rep_name, 'json')
    run_root = os.path.join(project_root, 'runs', branch)
    summary_csv = os.path.join(run_root, 'results', 'summary', 'summary_labels.csv')
    out_dir = os.path.join(run_root, 'results', 'ml_dataset')
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    labels = load_labels(summary_csv)
    out_path = os.path.join(out_dir, 'dataset_initial.csv')
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['case_name', 'branch_name', 'radius_mm', 'radius_norm', 'bend_amp',
                    'cell_size_mm', 'H0_mm', 'A0_mm2', 'max_stress_MPa',
                    'final_strain', 'final_stress_MPa'])
        for jp in sorted(glob.glob(os.path.join(json_dir, '*.json'))):
            data = json.load(open(jp, 'r'))
            name = data.get('case_name', os.path.splitext(os.path.basename(jp))[0])
            lab = labels.get(name, {})
            w.writerow([name, data.get('branch_name',''), data.get('radius_mm',''),
                        data.get('radius_norm',''), data.get('bend_amp',''),
                        data.get('cell_size_mm',''), data.get('H0_mm',''), data.get('A0_mm2',''),
                        lab.get('max_stress_MPa',''), lab.get('final_strain',''), lab.get('final_stress_MPa','')])
    print('Branch:', branch)
    print('Read JSON from:', json_dir)
    print('Wrote:', out_path)


if __name__ == '__main__':
    main()
