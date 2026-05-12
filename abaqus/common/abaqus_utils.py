# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import csv


def safe_mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def clean_name(name):
    base = os.path.splitext(os.path.basename(name))[0]
    return base.replace(' ', '_').replace('-', '_').replace('.', '_')


def write_csv_rows(csv_path, header, rows, append=False):
    import sys
    is_py2 = (sys.version_info[0] == 2)
    if is_py2:
        mode = 'ab' if append else 'wb'
        f = open(csv_path, mode)
    else:
        mode = 'a' if append else 'w'
        f = open(csv_path, mode, newline='')
    try:
        writer = csv.writer(f)
        if header is not None:
            writer.writerow(header)
        writer.writerows(rows)
    finally:
        f.close()


def write_id_list(f, ids, per_line=16):
    ids = list(ids)
    for i in range(0, len(ids), per_line):
        chunk = ids[i:i+per_line]
        f.write(', '.join(str(x) for x in chunk) + '\n')
