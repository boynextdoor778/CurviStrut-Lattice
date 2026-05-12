# -*- coding: utf-8 -*-
from __future__ import print_function
from abaqusConstants import *


def apply_material_and_static_step(model, material_name='Material-1', section_name='Section-1',
                                   e_modulus=2000.0, poisson_ratio=0.30,
                                   step_name='Step-1', time_period=1.0,
                                   initial_inc=0.01, min_inc=1e-8, max_inc=0.1,
                                   max_num_inc=1000):
    if material_name in model.materials.keys():
        del model.materials[material_name]
    mat = model.Material(name=material_name)
    mat.Elastic(table=((e_modulus, poisson_ratio),))

    if step_name in model.steps.keys():
        del model.steps[step_name]
    model.StaticStep(name=step_name, previous='Initial', nlgeom=ON,
                     timePeriod=time_period,
                     initialInc=initial_inc, maxNumInc=max_num_inc,
                     minInc=min_inc, maxInc=max_inc)
