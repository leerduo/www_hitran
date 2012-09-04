#!/usr/bin/env python
# find_iso_ZPE.py
import os
import sys

# Find and return a list of all the states in the hitranlbl_state table
# with energy = 0.
# The fields returned (to the standard output stream) are iso_id, iso_name,
# ID of the zero-point state, and the string representation of the zero-point
# state's quantum numbers. NB some isotopologues do not have a state with
# energy = 0., whilst others have more than one...

SETTINGS_PATH = '/Users/christian/research/VAMDC/HITRAN/django/HITRAN'
# Django needs to know where to find the HITRAN project's settings.py:
sys.path.append(SETTINGS_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Iso
from hitranlbl.models import State

isos = Iso.objects.all()
for iso in isos:
    zpe_states = State.objects.filter(iso=iso).filter(energy=0.)
    if not zpe_states:
        print '%d\t%s\tMISSING' % (iso.id, iso.iso_name)
    for zpe_state in zpe_states:
        print '%d\t%s\t%d\t%s' % (iso.id, iso.iso_name, zpe_state.id,
                                  zpe_state.s_qns)

