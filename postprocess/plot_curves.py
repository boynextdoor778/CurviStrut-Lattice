# -*- coding: utf-8 -*-
"""Plot stress-strain curves into PNG figures.

Usage:
    python postprocess/plot_curves.py tube_solid_222
    python postprocess/plot_curves.py tube_solid_444
"""
from __future__ import print_function
import os
import sys
import glob
import csv
import matplotlib.pyplot as plt


def get_project_root():
    if '__file__' in globals():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.getcwd()


def main():
    branch = sys.argv[1] if len(sys.argv) > 1 else 'tube_solid_222'
    project_root = get_project_root()
    run_root = os.path.join(project_root, 'runs', branch)
    curve_dir = os.path.join(run_root, 'results', 'curves')
    fig_dir = os.path.join(run_root, 'results', 'figures', 'stress_strain')
    if not os.path.isdir(fig_dir):
        os.makedirs(fig_dir)
    files = sorted(glob.glob(os.path.join(curve_dir, '*_stress_strain.csv')))
    for path in files:
        x, y = [], []
        with open(path, 'r') as f:
            r = csv.DictReader(f)
            for row in r:
                x.append(float(row['strain']))
                y.append(float(row['stress_MPa']))
        if not x:
            continue
        name = os.path.basename(path).replace('_stress_strain.csv','')
        plt.figure()
        plt.plot(x, y, linewidth=2)
        plt.xlabel('Strain')
        plt.ylabel('Stress (MPa)')
        plt.title(name)
        plt.grid(True)
        out = os.path.join(fig_dir, name + '.png')
        plt.savefig(out, dpi=200, bbox_inches='tight')
        plt.close()
        print('Wrote:', out)


if __name__ == '__main__':
    main()
