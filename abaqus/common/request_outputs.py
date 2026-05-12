# -*- coding: utf-8 -*-
from __future__ import print_function
from abaqusConstants import *


def clear_output_requests(model):
    for key in list(model.fieldOutputRequests.keys()):
        try:
            del model.fieldOutputRequests[key]
        except Exception:
            pass
    for key in list(model.historyOutputRequests.keys()):
        try:
            del model.historyOutputRequests[key]
        except Exception:
            pass


def request_rp_curve_output(model, assembly, step_name='Step-1', rp_set='RP_TOP_LOAD', frequency=1):
    model.FieldOutputRequest(name='F_RP_U_RF_CURVE', createStepName=step_name,
                             variables=('U', 'RF'), region=assembly.sets[rp_set],
                             frequency=frequency)


def request_contour_output(model, step_name='Step-1', frequency=LAST_INCREMENT,
                           variables=('S', 'U')):
    model.FieldOutputRequest(name='F_CONTOUR', createStepName=step_name,
                             variables=variables, frequency=frequency)
