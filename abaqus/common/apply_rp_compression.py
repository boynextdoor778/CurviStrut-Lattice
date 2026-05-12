# -*- coding: utf-8 -*-
from __future__ import print_function
from abaqusConstants import *
import regionToolset


def create_rp_set(assembly, set_name, point):
    if set_name in assembly.sets.keys():
        del assembly.sets[set_name]
    rp_feature = assembly.ReferencePoint(point=point)
    rp_obj = assembly.referencePoints[rp_feature.id]
    assembly.Set(name=set_name, referencePoints=(rp_obj,))
    return regionToolset.Region(referencePoints=(rp_obj,))


def apply_rp_compression(model, top_nodes_region, bottom_nodes_region, top_point, bottom_point,
                         disp_z, step_name='Step-1', rp_top_set='RP_TOP_LOAD',
                         rp_bottom_set='RP_BOTTOM_FIX'):
    a = model.rootAssembly
    rp_top_region = create_rp_set(a, rp_top_set, top_point)
    rp_bot_region = create_rp_set(a, rp_bottom_set, bottom_point)

    for name in ['COUPLE_TOP_TO_RP', 'COUPLE_BOTTOM_TO_RP']:
        if name in model.constraints.keys():
            del model.constraints[name]

    model.Coupling(name='COUPLE_TOP_TO_RP', controlPoint=rp_top_region,
                   surface=top_nodes_region, influenceRadius=WHOLE_SURFACE,
                   couplingType=KINEMATIC, localCsys=None,
                   u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    model.Coupling(name='COUPLE_BOTTOM_TO_RP', controlPoint=rp_bot_region,
                   surface=bottom_nodes_region, influenceRadius=WHOLE_SURFACE,
                   couplingType=KINEMATIC, localCsys=None,
                   u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    for name in ['BC_bottom_RP_fix', 'BC_top_RP_compress']:
        if name in model.boundaryConditions.keys():
            del model.boundaryConditions[name]

    model.DisplacementBC(name='BC_bottom_RP_fix', createStepName='Initial', region=rp_bot_region,
                         u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0)
    model.DisplacementBC(name='BC_top_RP_compress', createStepName=step_name, region=rp_top_region,
                         u1=0.0, u2=0.0, u3=disp_z, ur1=0.0, ur2=0.0, ur3=0.0)
