# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import json
import math
import sys

# Allow running from project root, from this script folder, or Abaqus/CAE noGUI.
def get_script_dir(script_name):
    if '__file__' in globals():
        return os.path.dirname(os.path.abspath(__file__))
    for arg in sys.argv:
        if script_name in arg:
            path = arg.split('=', 1)[-1]
            if os.path.isfile(path):
                return os.path.dirname(os.path.abspath(path))
    return os.path.abspath(os.path.join(os.getcwd(), 'abaqus', 'beam_branch'))


THIS_DIR = get_script_dir('build_beam_inp_from_centerline_json.py')
COMMON_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', 'common'))
if COMMON_DIR not in sys.path:
    sys.path.insert(0, COMMON_DIR)

from abaqus_utils import safe_mkdir, write_id_list


def _qkey(pt, tol):
    return (int(round(pt[0]/tol)), int(round(pt[1]/tol)), int(round(pt[2]/tol)))


def _dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def load_centerline_json(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)


def centerline_to_nodes_elements(data, tol=1e-6):
    nodes = []
    node_map = {}
    elements = []

    def get_node_id(pt):
        key = _qkey(pt, tol)
        if key in node_map:
            return node_map[key]
        node_id = len(nodes) + 1
        nodes.append((float(pt[0]), float(pt[1]), float(pt[2])))
        node_map[key] = node_id
        return node_id

    eid = 1
    for strut in data['struts']:
        pts = strut['points']
        for i in range(len(pts)-1):
            p1 = pts[i]
            p2 = pts[i+1]
            if _dist(p1, p2) <= tol:
                continue
            n1 = get_node_id(p1)
            n2 = get_node_id(p2)
            if n1 == n2:
                continue
            elements.append((eid, n1, n2))
            eid += 1
    return nodes, elements


def find_top_bottom_nodes(nodes, tol=1e-5):
    z_vals = [p[2] for p in nodes]
    z_min = min(z_vals)
    z_max = max(z_vals)
    top = [i+1 for i, p in enumerate(nodes) if abs(p[2]-z_max) <= tol]
    bottom = [i+1 for i, p in enumerate(nodes) if abs(p[2]-z_min) <= tol]
    if len(top) == 0 or len(bottom) == 0:
        raise RuntimeError('Cannot detect top/bottom nodes.')
    return top, bottom, z_min, z_max


def write_beam_inp(json_path, inp_path, e_modulus=2000.0, poisson_ratio=0.30,
                   compression_strain=0.20, step_time=1.0,
                   initial_inc=0.01, min_inc=1e-8, max_inc=0.1,
                   max_num_inc=1000, contour_frequency='LAST_INCREMENT'):
    data = load_centerline_json(json_path)
    nodes, elements = centerline_to_nodes_elements(data)
    top_nodes, bottom_nodes, z_min, z_max = find_top_bottom_nodes(nodes)

    radius = float(data.get('radius_mm', 1.0))
    h0 = float(data.get('H0_mm', z_max-z_min))
    a0 = float(data.get('A0_mm2', 1.0))
    disp_z = -compression_strain * h0

    xs = [p[0] for p in nodes]
    ys = [p[1] for p in nodes]
    x_mid = 0.5 * (min(xs) + max(xs))
    y_mid = 0.5 * (min(ys) + max(ys))
    rp_top = 900000001
    rp_bot = 900000002

    safe_mkdir(os.path.dirname(os.path.abspath(inp_path)))
    with open(inp_path, 'w') as f:
        f.write('*Heading\n')
        f.write('** Beam INP generated from: {}\n'.format(json_path))
        f.write('** H0_mm={}, A0_mm2={}, compression_strain={}\n'.format(h0, a0, compression_strain))
        f.write('*Preprint, echo=NO, model=NO, history=NO, contact=NO\n')
        f.write('*Part, name=LATTICE\n')
        f.write('*Node\n')
        for i, p in enumerate(nodes, start=1):
            f.write('{}, {:.8f}, {:.8f}, {:.8f}\n'.format(i, p[0], p[1], p[2]))
        f.write('*Element, type=B31, elset=EALL\n')
        for eid, n1, n2 in elements:
            f.write('{}, {}, {}\n'.format(eid, n1, n2))
        f.write('*Nset, nset=N_TOP_FIX\n')
        write_id_list(f, top_nodes)
        f.write('*Nset, nset=N_BOTTOM_FIX\n')
        write_id_list(f, bottom_nodes)
        f.write('*Beam Section, elset=EALL, material=Material-1, section=CIRC\n')
        f.write('{:.8f}\n'.format(radius))
        f.write('0., 0., -1.\n')
        f.write('*End Part\n')

        f.write('*Assembly, name=ASSEMBLY\n')
        f.write('*Instance, name=LATTICE-1, part=LATTICE\n')
        f.write('*End Instance\n')
        f.write('*Node\n')
        f.write('{}, {:.8f}, {:.8f}, {:.8f}\n'.format(rp_top, x_mid, y_mid, z_max))
        f.write('{}, {:.8f}, {:.8f}, {:.8f}\n'.format(rp_bot, x_mid, y_mid, z_min))
        f.write('*Nset, nset=RP_TOP_LOAD\n{}\n'.format(rp_top))
        f.write('*Nset, nset=RP_BOTTOM_FIX\n{}\n'.format(rp_bot))
        f.write('*Nset, nset=TOP_ASM_FIX, instance=LATTICE-1\n')
        write_id_list(f, top_nodes)
        f.write('*Nset, nset=BOTTOM_ASM_FIX, instance=LATTICE-1\n')
        write_id_list(f, bottom_nodes)
        f.write('*Surface, type=NODE, name=TOP_SURF\n')
        f.write('TOP_ASM_FIX, 1.0\n')
        f.write('*Surface, type=NODE, name=BOTTOM_SURF\n')
        f.write('BOTTOM_ASM_FIX, 1.0\n')
        f.write('*Coupling, constraint name=COUPLE_TOP_TO_RP, ref node={}, surface=TOP_SURF\n'.format(rp_top))
        f.write('*Kinematic\n')
        f.write('1, 6\n')
        f.write('*Coupling, constraint name=COUPLE_BOTTOM_TO_RP, ref node={}, surface=BOTTOM_SURF\n'.format(rp_bot))
        f.write('*Kinematic\n')
        f.write('1, 6\n')
        f.write('*End Assembly\n')

        f.write('*Material, name=Material-1\n')
        f.write('*Elastic\n')
        f.write('{:.8f}, {:.8f}\n'.format(e_modulus, poisson_ratio))
        f.write('*Step, name=Step-1, nlgeom=YES, inc={}\n'.format(max_num_inc))
        f.write('*Static\n')
        f.write('{:.8g}, {:.8g}, {:.8g}, {:.8g}\n'.format(initial_inc, step_time, min_inc, max_inc))
        f.write('*Boundary\n')
        f.write('RP_BOTTOM_FIX, 1, 6, 0.0\n')
        f.write('RP_TOP_LOAD, 1, 2, 0.0\n')
        f.write('RP_TOP_LOAD, 4, 6, 0.0\n')
        f.write('RP_TOP_LOAD, 3, 3, {:.8f}\n'.format(disp_z))
        # RP curve output every accepted increment.
        f.write('*Output, field, frequency=1\n')
        f.write('*Node Output, nset=RP_TOP_LOAD\n')
        f.write('U, RF\n')
        # Beam stress output. For large batches, LAST_INCREMENT is preferred.
        f.write('*Output, field, frequency={}\n'.format(contour_frequency))
        f.write('*Element Output, elset=EALL\n')
        f.write('S, E\n')
        f.write('*Node Output\n')
        f.write('U\n')
        f.write('*End Step\n')
    return {'case_name': data.get('case_name', os.path.splitext(os.path.basename(json_path))[0]),
            'h0': h0, 'a0': a0, 'num_nodes': len(nodes), 'num_elements': len(elements),
            'inp_path': inp_path}


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python build_beam_inp_from_centerline_json.py input.json output.inp')
        sys.exit(1)
    info = write_beam_inp(sys.argv[1], sys.argv[2])
    print('Wrote INP:', info['inp_path'])
    print('Nodes/elements:', info['num_nodes'], info['num_elements'])
