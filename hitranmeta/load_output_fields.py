#!/usr/bin/env python
# -*- coding: utf-8 -*-
# load_output_fields.py

# Christian Hill, 26/8/11
# Load up data to the OutputFields and OutputCollections tables of
# hitranmeta from the pyHAWKS application, where it is hard-coded in fmt_xn.py

import os
import sys

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
pyhawks_path = os.path.join(HOME, 'research/HITRAN/pyHAWKS')
sys.path.append(hitran_path)
sys.path.append(pyhawks_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import hitranmeta.models
from fmt_xn import *
import xn_utils

for trans_field in trans_fields:
    name = trans_field.name
    cfmt = trans_field.fmt
    ffmt = xn_utils.cfmt_to_ffmt(cfmt)
    prm_type = trans_field.prm_type.__name__
    try:
        # fmt is of the form '%1d', '%6.2f', '%1s'
        default = "' '*%d" % (int(float(cfmt[1:-1])))
    except ValueError:
        # unless the length is omitted for some reason
        default = ''
    desc = 'FILL ME'

    output_field = hitranmeta.models.OutputField(name=name, name_html=name,
            cfmt=cfmt, ffmt=ffmt, desc=desc, desc_html=desc,  default=default,
            prm_type=prm_type)
    output_field.save()

