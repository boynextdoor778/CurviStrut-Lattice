# -*- coding: utf-8 -*-
"""
Abaqus batch runner for CurviStrut-Lattice beam branch.

Run from project root:
    abaqus cae noGUI=abaqus/beam_branch/abaqus_batch_run_beam.py

This script:
    1) scans data/geometry_json/*.json
    2) converts each centerline JSON into a B31 beam INP
    3) submits the Abaqus job
    4) reads RP U/RF from the ODB
    5) exports force-displacement and stress-strain CSV files
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
    """Return script folder in Abaqus/CAE noGUI, where __file__ may be undefined."""
    if '__file__' in globals():
        return os.path.dirname(os.path.abspath(__file__))

    # Abaqus often stores the noGUI script path in sys.argv as noGUI=path or as path.
    for arg in sys.argv:
        if script_name in arg:
            path = arg.split('=', 1)[-1]
            if os.path.isfile(path):
                return os.path.dirname(os.path.abspath(path))

    # Fallback for the recommended command: run from project root.
    return os.path.abspath(os.path.join(os.getcwd(), 'abaqus', 'beam_branch'))


THIS_DIR = get_script_dir('abaqus_batch_run_beam.py')
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, '..', '..'))
COMMON_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', 'common'))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)
if COMMON_DIR not in sys.path:
    sys.path.insert(0, COMMON_DIR)

from build_beam_inp_from_centerline_json import write_beam_inp, load_centerline_json
from abaqus_utils import safe_mkdir, clean_name, write_csv_rows
from extract_rp_curves import extract_rp_curves_from_odb

# ---------------- USER SETTINGS ----------------
JSON_DIR = os.path.join(PROJECT_ROOT, 'data', 'geometry_json')
# Backward-compatible fallback for early scaffold versions that accidentally exported
# JSON files under matlab/02_repeat_lattice/data/geometry_json.
JSON_DIR_FALLBACK = os.path.join(PROJECT_ROOT, 'matlab', '02_repeat_lattice', 'data', 'geometry_json')
INP_DIR = os.path.join(PROJECT_ROOT, 'output', 'inp')
WORK_ROOT = os.path.join(PROJECT_ROOT, 'abaqus_work_beam')
RESULT_ROOT = os.path.join(PROJECT_ROOT, 'results', 'curves')
SUMMARY_ROOT = os.path.join(PROJECT_ROOT, 'results', 'summary')
SCRATCH_ROOT = os.path.join(PROJECT_ROOT, 'abaqus_scratch_beam')

COMPRESSION_STRAIN = 0.20
E_MODULUS = 2000.0
POISSON_RATIO = 0.30
STEP_TIME = 1.0
INITIAL_INC = 0.01
MAX_INC = 0.1
MIN_INC = 1e-8
MAX_NUM_INC = 1000
CONTOUR_FREQUENCY = 'LAST_INCREMENT'

NUM_CPUS = 8
NUM_DOMAINS = 8
MEMORY_PERCENT = 90
MAX_CASES = 2      # use None for all cases after testing
SKIP_IF_RESULT_EXISTS = True
STOP_ON_ERROR = False
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
    path = os.path.join(SUMMARY_ROOT, 'beam_batch_status.csv')
    exists = os.path.isfile(path)
    header = None if exists else ['case_name', 'status', 'message', 'elapsed_sec', 'odb_mb', 'nodes', 'elements']
    write_csv_rows(path, header, [row], append=exists)


def run_one(json_path):
    t0 = time.time()
    data = load_centerline_json(json_path)
    case_name = clean_name(data.get('case_name', json_path))
    inp_path = os.path.join(INP_DIR, case_name + '.inp')
    work_dir = os.path.join(WORK_ROOT, case_name)
    job_name = 'Job_' + case_name

    safe_mkdir(INP_DIR)
    safe_mkdir(WORK_ROOT)
    safe_mkdir(RESULT_ROOT)
    safe_mkdir(SCRATCH_ROOT)
    safe_mkdir(work_dir)

    if SKIP_IF_RESULT_EXISTS and result_exists(case_name):
        print('Skipping existing result:', case_name)
        append_status([case_name, 'SKIPPED', 'Result exists', '', '', '', ''])
        return 'SKIPPED'

    info = write_beam_inp(json_path, inp_path,
                          e_modulus=E_MODULUS,
                          poisson_ratio=POISSON_RATIO,
                          compression_strain=COMPRESSION_STRAIN,
                          step_time=STEP_TIME,
                          initial_inc=INITIAL_INC,
                          min_inc=MIN_INC,
                          max_inc=MAX_INC,
                          max_num_inc=MAX_NUM_INC,
                          contour_frequency=CONTOUR_FREQUENCY)

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
                                              step_name='Step-1', rp_set='RP_TOP_LOAD')
        elapsed = round(time.time() - t0, 3)
        odb_mb = round(os.path.getsize(odb_path)/(1024.0*1024.0), 3) if os.path.isfile(odb_path) else ''
        append_status([case_name, 'SUCCESS', 'frames={}'.format(n_frames), elapsed, odb_mb,
                       info['num_nodes'], info['num_elements']])
        return 'SUCCESS'
    except Exception as e:
        elapsed = round(time.time() - t0, 3)
        print(traceback.format_exc())
        append_status([case_name, 'FAILED', str(e), elapsed, '', info.get('num_nodes',''), info.get('num_elements','')])
        if STOP_ON_ERROR:
            raise
        return 'FAILED'
    finally:
        try:
            os.chdir(old_cwd)
        except Exception:
            pass


def main():
    files = sorted(glob.glob(os.path.join(JSON_DIR, '*.json')))
    if len(files) == 0 and os.path.isdir(JSON_DIR_FALLBACK):
        print('WARNING: No JSON in project data/geometry_json. Using fallback:', JSON_DIR_FALLBACK)
        files = sorted(glob.glob(os.path.join(JSON_DIR_FALLBACK, '*.json')))
    if MAX_CASES is not None:
        files = files[:MAX_CASES]
    print('CurviStrut beam batch')
    print('JSON dir:', JSON_DIR)
    print('Found:', len(files))
    if len(files) == 0:
        raise RuntimeError('No JSON files found. Run MATLAB generation/repetition first.')
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
