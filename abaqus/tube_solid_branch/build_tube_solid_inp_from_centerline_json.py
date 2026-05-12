# -*- coding: utf-8 -*-
"""
Build a lightweight solid-tube Abaqus INP from CurviStrut centerline JSON.

This branch is a practical middle route between:
    beam branch       : fast, line/beam elements, good for large datasets
    voxel solid branch: very heavy, but gives solid stress contours

Here each curved strut is converted into a polygonal solid rod made from C3D6
wedge elements. Strut end sections are kinematically coupled to shared junction
nodes so repeated-cell junctions stay connected without expensive Boolean merge.

This is not a CAD Boolean swept-solid model. It is a direct solid mesh generator
that is much more stable for batch use.
"""
from __future__ import print_function

import os
import sys
import json
import math


def get_script_dir(script_name):
    if '__file__' in globals():
        return os.path.dirname(os.path.abspath(__file__))
    for arg in sys.argv:
        if script_name in arg:
            path = arg.split('=', 1)[-1]
            if os.path.isfile(path):
                return os.path.dirname(os.path.abspath(path))
    return os.path.abspath(os.path.join(os.getcwd(), 'abaqus', 'tube_solid_branch'))


THIS_DIR = get_script_dir('build_tube_solid_inp_from_centerline_json.py')
COMMON_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', 'common'))
if COMMON_DIR not in sys.path:
    sys.path.insert(0, COMMON_DIR)

from abaqus_utils import safe_mkdir, write_id_list


# ------------------------------------------------------------
# vector utilities
# ------------------------------------------------------------

def v_add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])


def v_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def v_mul(a, s):
    return (a[0]*s, a[1]*s, a[2]*s)


def v_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def v_cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def v_norm(a):
    return math.sqrt(v_dot(a, a))


def v_unit(a, fallback=(1.0, 0.0, 0.0)):
    n = v_norm(a)
    if n < 1e-12:
        return fallback
    return (a[0]/n, a[1]/n, a[2]/n)


def dist(a, b):
    return v_norm(v_sub(a, b))


def qkey(pt, tol):
    return (int(round(pt[0]/tol)), int(round(pt[1]/tol)), int(round(pt[2]/tol)))


# ------------------------------------------------------------
# geometry and mesh
# ------------------------------------------------------------

def load_centerline_json(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)


def downsample_points(points, axial_step):
    axial_step = max(1, int(axial_step))
    out = []
    for i, p in enumerate(points):
        if i == 0 or i == len(points)-1 or (i % axial_step == 0):
            pp = (float(p[0]), float(p[1]), float(p[2]))
            if len(out) == 0 or dist(out[-1], pp) > 1e-9:
                out.append(pp)
    if len(out) < 2:
        raise RuntimeError('A strut path has fewer than two usable points.')
    return out


def tangents_for_path(points):
    tangents = []
    n = len(points)
    for i in range(n):
        if i == 0:
            t = v_sub(points[1], points[0])
        elif i == n-1:
            t = v_sub(points[-1], points[-2])
        else:
            t = v_sub(points[i+1], points[i-1])
        tangents.append(v_unit(t, fallback=(0.0, 0.0, 1.0)))
    return tangents


def frames_for_path(points):
    """Build low-twist section frames along a path by simple parallel projection."""
    tangents = tangents_for_path(points)
    t0 = tangents[0]
    # Pick an initial reference axis not parallel to tangent.
    ref = (0.0, 0.0, 1.0)
    if abs(v_dot(ref, t0)) > 0.90:
        ref = (1.0, 0.0, 0.0)
    n0 = v_unit(v_cross(ref, t0), fallback=(1.0, 0.0, 0.0))
    b0 = v_unit(v_cross(t0, n0), fallback=(0.0, 1.0, 0.0))

    normals = [n0]
    binormals = [b0]
    prev_n = n0
    for i in range(1, len(points)):
        t = tangents[i]
        # Project previous normal onto plane perpendicular to current tangent.
        ni = v_sub(prev_n, v_mul(t, v_dot(prev_n, t)))
        if v_norm(ni) < 1e-10:
            ref = (0.0, 0.0, 1.0)
            if abs(v_dot(ref, t)) > 0.90:
                ref = (1.0, 0.0, 0.0)
            ni = v_cross(ref, t)
        ni = v_unit(ni)
        bi = v_unit(v_cross(t, ni))
        normals.append(ni)
        binormals.append(bi)
        prev_n = ni
    return tangents, normals, binormals


def build_tube_mesh(data, ring_segments=8, axial_step=2, merge_tol=1e-5):
    """Return nodes, elements, end section node sets, and unique junction nodes.

    nodes/elements are part-level solid mesh data.
    junction nodes are assembly-level nodes used as rigid joint control nodes.
    """
    ring_segments = max(6, int(ring_segments))
    radius = float(data.get('radius_mm', 1.0))

    nodes = []
    elements = []
    end_sections = []   # dict: name, part_nodes, junction_key
    junction_points = {}

    def add_node(pt):
        nodes.append((float(pt[0]), float(pt[1]), float(pt[2])))
        return len(nodes)

    eid = 1
    end_id = 1
    for sidx, strut in enumerate(data['struts'], start=1):
        pts = downsample_points(strut['points'], axial_step)
        tangents, normals, binormals = frames_for_path(pts)

        section_nodes = []
        for i, c in enumerate(pts):
            center_id = add_node(c)
            ring_ids = []
            nvec = normals[i]
            bvec = binormals[i]
            for j in range(ring_segments):
                theta = 2.0 * math.pi * float(j) / float(ring_segments)
                offset = v_add(v_mul(nvec, radius * math.cos(theta)),
                               v_mul(bvec, radius * math.sin(theta)))
                ring_ids.append(add_node(v_add(c, offset)))
            section_nodes.append([center_id] + ring_ids)

        for i in range(len(pts)-1):
            sec0 = section_nodes[i]
            sec1 = section_nodes[i+1]
            c0 = sec0[0]
            c1 = sec1[0]
            for j in range(ring_segments):
                j2 = (j + 1) % ring_segments
                # C3D6 wedge: lower triangle, upper triangle.
                n1 = c0
                n2 = sec0[1 + j]
                n3 = sec0[1 + j2]
                n4 = c1
                n5 = sec1[1 + j]
                n6 = sec1[1 + j2]
                elements.append((eid, n1, n2, n3, n4, n5, n6))
                eid += 1

        for end_label, sec in [('START', section_nodes[0]), ('END', section_nodes[-1])]:
            pt = pts[0] if end_label == 'START' else pts[-1]
            key = qkey(pt, merge_tol)
            if key not in junction_points:
                junction_points[key] = pt
            end_sections.append({
                'name': 'END_{:06d}_{}'.format(end_id, end_label),
                'nodes': sec,
                'junction_key': key,
                'point': pt,
            })
            end_id += 1

    # Assign assembly node IDs to junction control nodes.
    junctions = []
    base_id = 800000001
    for idx, key in enumerate(sorted(junction_points.keys()), start=0):
        junctions.append({
            'key': key,
            'node_id': base_id + idx,
            'point': junction_points[key],
        })
    junction_id_by_key = dict((j['key'], j['node_id']) for j in junctions)

    return {
        'nodes': nodes,
        'elements': elements,
        'end_sections': end_sections,
        'junctions': junctions,
        'junction_id_by_key': junction_id_by_key,
        'radius': radius,
        'ring_segments': ring_segments,
    }


# ------------------------------------------------------------
# INP writer
# ------------------------------------------------------------

def _clean_name(name):
    return os.path.splitext(os.path.basename(str(name)))[0].replace(' ', '_').replace('-', '_')


def _write_nset_and_surface(f, nset_name, surface_name, ids, instance_name=None):
    if instance_name is None:
        f.write('*Nset, nset={}\n'.format(nset_name))
    else:
        f.write('*Nset, nset={}, instance={}\n'.format(nset_name, instance_name))
    write_id_list(f, ids)
    f.write('*Surface, type=NODE, name={}\n'.format(surface_name))
    f.write('{}, 1.0\n'.format(nset_name))


def write_tube_solid_inp(json_path, inp_path,
                         e_modulus=2000.0, poisson_ratio=0.30,
                         compression_strain=0.20, step_time=1.0,
                         initial_inc=0.01, min_inc=1e-8, max_inc=0.1,
                         max_num_inc=1000, contour_frequency='LAST_INCREMENT',
                         ring_segments=8, axial_step=2):
    data = load_centerline_json(json_path)
    mesh = build_tube_mesh(data, ring_segments=ring_segments, axial_step=axial_step)

    nodes = mesh['nodes']
    elements = mesh['elements']
    end_sections = mesh['end_sections']
    junctions = mesh['junctions']
    junction_id_by_key = mesh['junction_id_by_key']

    xs = [p[0] for p in nodes]
    ys = [p[1] for p in nodes]
    zs = [p[2] for p in nodes]
    z_min = min(zs)
    z_max = max(zs)
    x_mid = 0.5 * (min(xs) + max(xs))
    y_mid = 0.5 * (min(ys) + max(ys))

    h0 = float(data.get('H0_mm', z_max - z_min))
    a0 = float(data.get('A0_mm2', max(1.0, (max(xs)-min(xs))*(max(ys)-min(ys)))))
    disp_z = -float(compression_strain) * h0

    # Top/bottom junctions are selected by original junction coordinates, not tube surface nodes.
    j_z = [j['point'][2] for j in junctions]
    j_z_min = min(j_z)
    j_z_max = max(j_z)
    top_junctions = [j['node_id'] for j in junctions if abs(j['point'][2] - j_z_max) <= 1e-5]
    bottom_junctions = [j['node_id'] for j in junctions if abs(j['point'][2] - j_z_min) <= 1e-5]
    if len(top_junctions) == 0 or len(bottom_junctions) == 0:
        raise RuntimeError('Cannot detect top/bottom junction nodes.')

    # In v5 we do NOT create a second-level global RP coupling.
    # Earlier v4 coupled top/bottom junction control nodes to another RP,
    # which can create nested kinematic constraints and cause Abaqus jobs
    # to stop before writing valid Step data.  Compression is now applied
    # directly to the top/bottom junction control node sets.

    safe_mkdir(os.path.dirname(os.path.abspath(inp_path)))
    with open(inp_path, 'w') as f:
        f.write('*Heading\n')
        f.write('** Tube-solid INP generated from: {}\n'.format(json_path))
        f.write('** This is a direct C3D6 solid tube mesh, not CAD Boolean sweep.\n')
        f.write('** ring_segments={}, axial_step={}\n'.format(ring_segments, axial_step))
        f.write('** H0_mm={}, A0_mm2={}, compression_strain={}\n'.format(h0, a0, compression_strain))
        f.write('*Preprint, echo=NO, model=NO, history=NO, contact=NO\n')

        # Part-level solid mesh.
        f.write('*Part, name=LATTICE\n')
        f.write('*Node\n')
        for i, p in enumerate(nodes, start=1):
            f.write('{}, {:.8f}, {:.8f}, {:.8f}\n'.format(i, p[0], p[1], p[2]))
        f.write('*Element, type=C3D6, elset=EALL\n')
        for e in elements:
            f.write('{}, {}, {}, {}, {}, {}, {}\n'.format(*e))
        f.write('*Solid Section, elset=EALL, material=Material-1\n')
        f.write(',\n')
        f.write('*End Part\n')

        # Assembly.
        f.write('*Assembly, name=ASSEMBLY\n')
        f.write('*Instance, name=LATTICE-1, part=LATTICE\n')
        f.write('*End Instance\n')

        # Assembly nodes: shared junction control nodes only.
        # v7 removes the previous global RP nodes to avoid nested kinematic coupling.
        f.write('*Node\n')
        for j in junctions:
            p = j['point']
            f.write('{}, {:.8f}, {:.8f}, {:.8f}\n'.format(j['node_id'], p[0], p[1], p[2]))
        f.write('*Nset, nset=JUNCTION_ALL\n')
        write_id_list(f, [j['node_id'] for j in junctions])
        f.write('*Nset, nset=JUNCTION_TOP\n')
        write_id_list(f, top_junctions)
        f.write('*Nset, nset=JUNCTION_BOTTOM\n')
        write_id_list(f, bottom_junctions)

        # End-section surfaces and couplings to shared junction control nodes.
        for idx, sec in enumerate(end_sections, start=1):
            nset_name = sec['name']
            surf_name = 'SURF_' + nset_name
            _write_nset_and_surface(f, nset_name, surf_name, sec['nodes'], instance_name='LATTICE-1')
            jnode = junction_id_by_key[sec['junction_key']]
            f.write('*Coupling, constraint name=CPL_{:06d}, ref node={}, surface={}\n'.format(idx, jnode, surf_name))
            f.write('*Kinematic\n')
            f.write('1, 6\n')

        # No global RP layer in v7.
        # Boundary conditions are applied directly to JUNCTION_TOP and JUNCTION_BOTTOM.
        f.write('*End Assembly\n')

        # Material and step.
        f.write('*Material, name=Material-1\n')
        f.write('*Elastic\n')
        f.write('{:.8f}, {:.8f}\n'.format(e_modulus, poisson_ratio))
        f.write('*Step, name=Step-1, nlgeom=YES, inc={}\n'.format(max_num_inc))
        f.write('*Static\n')
        f.write('{:.8g}, {:.8g}, {:.8g}, {:.8g}\n'.format(initial_inc, step_time, min_inc, max_inc))
        f.write('*Boundary\n')
        f.write('JUNCTION_BOTTOM, 1, 6, 0.0\n')
        f.write('JUNCTION_TOP, 1, 2, 0.0\n')
        f.write('JUNCTION_TOP, 4, 6, 0.0\n')
        f.write('JUNCTION_TOP, 3, 3, {:.8f}\n'.format(disp_z))

        # Outputs: top-junction curve every accepted increment; full stress usually final only.
        f.write('*Output, field, frequency=1\n')
        f.write('*Node Output, nset=JUNCTION_TOP\n')
        f.write('U, RF\n')
        # Whole-model contour output.
        # For INP keyword syntax, Abaqus expects integer frequency.
        # The Abaqus Python constant LAST_INCREMENT is not valid inside raw .inp.
        # Use NUMBER INTERVAL=1 to request the last frame only.
        if str(contour_frequency).upper() in ('LAST_INCREMENT', 'LAST', 'FINAL'):
            f.write('*Output, field, number interval=1\n')
        else:
            f.write('*Output, field, frequency={}\n'.format(int(contour_frequency)))
        # EALL is a part-level element set. In the Step block, Abaqus expects
        # an assembly-level set if an elset is specified. To avoid the
        # 'ELEMENT SET ASSEMBLY_EALL HAS NOT BEEN DEFINED' input error,
        # request element output for the whole model instead of naming EALL here.
        f.write('*Element Output\n')
        f.write('S, E\n')
        f.write('*Node Output\n')
        f.write('U\n')
        f.write('*End Step\n')

    return {
        'case_name': data.get('case_name', _clean_name(json_path)),
        'h0': h0,
        'a0': a0,
        'num_nodes': len(nodes),
        'num_elements': len(elements),
        'num_junctions': len(junctions),
        'num_end_couplings': len(end_sections),
        'inp_path': inp_path,
    }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: abaqus python build_tube_solid_inp_from_centerline_json.py input.json output.inp')
        sys.exit(1)
    info = write_tube_solid_inp(sys.argv[1], sys.argv[2])
    print('Wrote INP:', info['inp_path'])
    print('Nodes/elements/junctions:', info['num_nodes'], info['num_elements'], info['num_junctions'])
