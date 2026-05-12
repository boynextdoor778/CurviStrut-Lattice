# -*- coding: utf-8 -*-
"""
Abaqus batch runner for CurviStrut-Lattice tube-solid branch (444).

Run from project root:
    abaqus cae noGUI=abaqus/tube_solid_branch/abaqus_batch_run_tube_solid_444.py

This script:
    1) scans data/rep444/json/*_rep444.json
    2) converts each centerline JSON into a direct C3D6 tube-solid INP
    3) submits the Abaqus job from the INP
    4) extracts top-junction U/RF curves from the ODB

Recommended first test:
    MAX_CASES = 1
    RING_SEGMENTS = 8
    AXIAL_STEP = 3
    CONTOUR_FREQUENCY = 'LAST_INCREMENT'
"""
from __future__ import print_function

import os
import sys
import glob
import time
import traceback

from abaqus import mdb
from abaqusConstants import *


def get_script_dir(script_name):
    if '__file__' in globals():
        return os.path.dirname(os.path.abspath(__file__))
    for arg in sys.argv:
        if script_name in arg:
            path = arg.split('=', 1)[-1]
            if os.path.isfile(path):
                return os.path.dirname(os.path.abspath(path))
    return os.path.abspath(os.path.join(os.getcwd(), 'abaqus', 'tube_solid_branch'))


THIS_DIR = get_script_dir('abaqus_batch_run_tube_solid_444.py')
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, '..', '..'))
COMMON_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', 'common'))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)
if COMMON_DIR not in sys.path:
    sys.path.insert(0, COMMON_DIR)

from build_tube_solid_inp_from_centerline_json import write_tube_solid_inp, load_centerline_json
from abaqus_utils import safe_mkdir, clean_name, write_csv_rows
from extract_rp_curves import extract_rp_curves_from_odb

# ---------------- USER SETTINGS ----------------
RUN_ROOT = os.path.join(PROJECT_ROOT, 'runs', 'tube_solid_444')
JSON_DIR = os.path.join(PROJECT_ROOT, 'data', 'rep444', 'json')
INP_DIR = os.path.join(RUN_ROOT, 'inp')
WORK_ROOT = os.path.join(RUN_ROOT, 'work')
RESULT_ROOT = os.path.join(RUN_ROOT, 'results', 'curves')
SUMMARY_ROOT = os.path.join(RUN_ROOT, 'results', 'summary')
SCRATCH_ROOT = os.path.join(RUN_ROOT, 'scratch')

BRANCH_NAME = '4x4x4'
JSON_PATTERN = '*_rep444.json'
SUMMARY_FILE = 'tube_solid_444_batch_status.csv'

COMPRESSION_STRAIN = 0.20
E_MODULUS = 2000.0
POISSON_RATIO = 0.30

# Keep this compact for first solid tests. Increase only after one 222 case succeeds.
STEP_TIME = 1.0
INITIAL_INC = 0.01
MAX_INC = 0.1
MIN_INC = 1e-8
MAX_NUM_INC = 1000
CONTOUR_FREQUENCY = 'LAST_INCREMENT'  # for 444, do not use 1 unless you accept very large ODBs

# Tube mesh resolution for 444. Keep compact unless the first 444 case is confirmed stable.
RING_SEGMENTS = 8
AXIAL_STEP = 3       # if 444 is too slow, try 4; for smoother geometry try 2

NUM_CPUS = 8
NUM_DOMAINS = 8
MEMORY_PERCENT = 90
MAX_CASES = 1        # keep 1 for 444 test; set None only after validation
SKIP_IF_RESULT_EXISTS = True
STOP_ON_ERROR = False
# v5 note: tube-solid compression is applied directly on JUNCTION_TOP/BOTTOM
# control nodes. This avoids nested kinematic coupling and prevents empty ODB Step data.
# ------------------------------------------------


def check_sta_success(sta_path):
    if not os.path.isfile(sta_path):
        return False, 'STA file not found'
    text = open(sta_path, 'r').read().upper()
    if 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' in text:
        return True, 'STA success'
    if 'ERROR' in text or 'THE ANALYSIS HAS NOT BEEN COMPLETED' in text:
        return False, 'STA reports error or incomplete analysis'
    return False, 'STA success message not found'


def result_exists(case_name):
    return os.path.isfile(os.path.join(RESULT_ROOT, case_name + '_stress_strain.csv'))


def append_status(row):
    safe_mkdir(SUMMARY_ROOT)
    path = os.path.join(SUMMARY_ROOT, SUMMARY_FILE)
    exists = os.path.isfile(path)
    header = None if exists else [
        'case_name', 'status', 'message', 'elapsed_sec', 'odb_mb',
        'nodes', 'elements', 'junctions', 'end_couplings'
    ]
    write_csv_rows(path, header, [row], append=exists)


def run_one(json_path):
    t0 = time.time()
    data = load_centerline_json(json_path)
    case_name = clean_name(data.get('case_name', json_path))
    inp_path = os.path.join(INP_DIR, case_name + '_tube_solid.inp')
    work_dir = os.path.join(WORK_ROOT, case_name)
    job_name = 'Job_' + case_name + '_tube'

    safe_mkdir(INP_DIR)
    safe_mkdir(WORK_ROOT)
    safe_mkdir(RESULT_ROOT)
    safe_mkdir(SCRATCH_ROOT)
    safe_mkdir(work_dir)

    if SKIP_IF_RESULT_EXISTS and result_exists(case_name):
        print('Skipping existing result:', case_name)
        append_status([case_name, 'SKIPPED', 'Result exists', '', '', '', '', '', ''])
        return 'SKIPPED'

    info = write_tube_solid_inp(json_path, inp_path,
                                e_modulus=E_MODULUS,
                                poisson_ratio=POISSON_RATIO,
                                compression_strain=COMPRESSION_STRAIN,
                                step_time=STEP_TIME,
                                initial_inc=INITIAL_INC,
                                min_inc=MIN_INC,
                                max_inc=MAX_INC,
                                max_num_inc=MAX_NUM_INC,
                                contour_frequency=CONTOUR_FREQUENCY,
                                ring_segments=RING_SEGMENTS,
                                axial_step=AXIAL_STEP)

    old_cwd = os.getcwd()
    try:
        os.chdir(work_dir)
        if job_name in mdb.jobs.keys():
            del mdb.jobs[job_name]
        job = mdb.JobFromInputFile(name=job_name, inputFileName=inp_path,
                                   type=ANALYSIS, memory=MEMORY_PERCENT,
                                   memoryUnits=PERCENTAGE, scratch=SCRATCH_ROOT,
                                   multiprocessingMode=DEFAULT,
                                   numCpus=NUM_CPUS, numDomains=NUM_DOMAINS,
                                   explicitPrecision=SINGLE,
                                   nodalOutputPrecision=SINGLE)
        print('Submitting:', job_name)
        job.submit(consistencyChecking=OFF)
        job.waitForCompletion()
        print('Finished:', job_name)

        sta_path = os.path.join(work_dir, job_name + '.sta')
        ok, msg = check_sta_success(sta_path)
        if not ok:
            raise RuntimeError(msg)

        odb_path = os.path.join(work_dir, job_name + '.odb')
        n_frames = extract_rp_curves_from_odb(odb_path, RESULT_ROOT, case_name,
                                              info['h0'], info['a0'],
                                              step_name='Step-1', rp_set='JUNCTION_TOP')
        elapsed = round(time.time() - t0, 3)
        odb_mb = round(os.path.getsize(odb_path)/(1024.0*1024.0), 3) if os.path.isfile(odb_path) else ''
        append_status([case_name, 'SUCCESS', 'frames={}'.format(n_frames), elapsed, odb_mb,
                       info['num_nodes'], info['num_elements'],
                       info['num_junctions'], info['num_end_couplings']])
        return 'SUCCESS'
    except Exception as e:
        elapsed = round(time.time() - t0, 3)
        print(traceback.format_exc())
        append_status([case_name, 'FAILED', str(e), elapsed, '',
                       info.get('num_nodes',''), info.get('num_elements',''),
                       info.get('num_junctions',''), info.get('num_end_couplings','')])
        if STOP_ON_ERROR:
            raise
        return 'FAILED'
    finally:
        try:
            os.chdir(old_cwd)
        except Exception:
            pass


def main():
    files = sorted(glob.glob(os.path.join(JSON_DIR, JSON_PATTERN)))
    active_json_dir = JSON_DIR
    if MAX_CASES is not None:
        files = files[:MAX_CASES]
    print('CurviStrut tube-solid batch (444)')
    print('JSON dir:', active_json_dir)
    print('Run root:', RUN_ROOT)
    print('JSON pattern:', JSON_PATTERN)
    print('Found:', len(files))
    print('ring_segments={}, axial_step={}, contour_frequency={}'.format(
        RING_SEGMENTS, AXIAL_STEP, CONTOUR_FREQUENCY))
    if len(files) == 0:
        raise RuntimeError('No *_rep444.json files found. Run batch_repeat444_centerline first.')

    n_success = n_failed = n_skipped = 0
    for idx, path in enumerate(files):
        print('\n========== [{}/{}] {} =========='.format(idx+1, len(files), os.path.basename(path)))
        status = run_one(path)
        if status == 'SUCCESS':
            n_success += 1
        elif status == 'SKIPPED':
            n_skipped += 1
        else:
            n_failed += 1
    print('\nDONE | success={} skipped={} failed={}'.format(n_success, n_skipped, n_failed))


if __name__ == '__main__':
    main()
