#!/usr/bin/env python
# blank_DCl_fields.py
import os
import sys

SETTINGS_PATH = '/Users/christian/research/VAMDC/HITRAN/django/HITRAN'
# Django needs to know where to find the HITRAN project's settings.py:
sys.path.append(SETTINGS_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Iso
from hitranlbl.models import Trans

isos = Iso.objects.filter(pk__in=(107,108))
transitions = Trans.objects.filter(iso__in=isos)

for transition in transitions:
    #print transition.par_line
    print transition.id,':',transition.par_line
    par_line = transition.par_line[:35] + '     '\
                 + transition.par_line[40:55] + '            '\
                 + transition.par_line[67:]
    transition.par_line = par_line
    transition.save()

