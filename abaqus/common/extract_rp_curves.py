# -*- coding: utf-8 -*-
from __future__ import print_function
from abaqus import session
from abaqusConstants import NODAL
import os

from abaqus_utils import write_csv_rows, safe_mkdir


def find_repo_key(repo, target_name):
    if target_name in repo.keys():
        return target_name
    target_upper = target_name.upper()
    for k in repo.keys():
        if k.upper() == target_upper:
            return k
    raise KeyError('Cannot find key "{}". Available keys: {}'.format(target_name, list(repo.keys())))


def extract_rp_curves_from_odb(odb_path, result_root, case_name, h0, a0,
                               step_name='Step-1', rp_set='RP_TOP_LOAD'):
    if not os.path.isfile(odb_path):
        raise IOError('ODB file not found: {}'.format(odb_path))
    safe_mkdir(result_root)

    odb = session.openOdb(name=odb_path)
    try:
        step = odb.steps[step_name]
        asm = odb.rootAssembly
        set_key = find_repo_key(asm.nodeSets, rp_set)
        region = asm.nodeSets[set_key]

        rows_fd = []
        rows_ss = []
        rows_all = []

        for frame in step.frames:
            if 'U' not in frame.fieldOutputs.keys() or 'RF' not in frame.fieldOutputs.keys():
                continue
            u_field = frame.fieldOutputs['U'].getSubset(region=region, position=NODAL)
            rf_field = frame.fieldOutputs['RF'].getSubset(region=region, position=NODAL)
            u3_vals = [v.data[2] for v in u_field.values]
            rf3_vals = [v.data[2] for v in rf_field.values]
            if len(u3_vals) == 0 or len(rf3_vals) == 0:
                continue
            avg_u3 = sum(u3_vals) / float(len(u3_vals))
            sum_rf3 = sum(rf3_vals)
            displacement = -avg_u3
            force = -sum_rf3
            strain = -avg_u3 / float(h0)
            stress = -sum_rf3 / float(a0)
            rows_fd.append([displacement, force])
            rows_ss.append([strain, stress])
            rows_all.append([frame.frameValue, avg_u3, sum_rf3, displacement, force, strain, stress])

        if len(rows_ss) == 0:
            raise RuntimeError('No valid U/RF data extracted from {}'.format(odb_path))

        fd_csv = os.path.join(result_root, case_name + '_force_displacement.csv')
        ss_csv = os.path.join(result_root, case_name + '_stress_strain.csv')
        all_csv = os.path.join(result_root, case_name + '_all_response.csv')
        write_csv_rows(fd_csv, ['displacement_mm', 'force_N'], rows_fd)
        write_csv_rows(ss_csv, ['strain', 'stress_MPa'], rows_ss)
        write_csv_rows(all_csv, ['time', 'avg_u3_mm', 'sum_rf3_N', 'displacement_mm', 'force_N', 'strain', 'stress_MPa'], rows_all)
        return len(rows_ss)
    finally:
        odb.close()
