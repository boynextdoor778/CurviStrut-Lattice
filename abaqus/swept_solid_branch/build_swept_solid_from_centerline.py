# -*- coding: utf-8 -*-
"""
Swept-solid branch scaffold.

This file is intentionally not a production-ready generator yet. In Abaqus/CAE,
robust swept-solid generation needs validation for:

1) curve creation from centerline points,
2) circular profile sweep along each curve,
3) intersection / merge / tie treatment at strut junctions,
4) meshing strategy,
5) top/bottom surface or node-set detection.

Recommended use:
    - first validate one 1x1x1 unit cell manually,
    - then implement batch swept-solid generation,
    - use swept-solid only for representative display/validation samples.
"""
from __future__ import print_function


def build_swept_solid_from_centerline(json_path, model_name):
    raise NotImplementedError(
        'Swept-solid generation is a scaffold. Validate Abaqus geometry operations first.'
    )
