#!/usr/bin/env python
# load_iso_ZPE.py
import os
import sys

# Load up the state IDs of the zero-point levels for each isotopologue listed
# in the file ZPE_state_ids.txt, produced by find_iso_ZPE.py. This file must
# be edited so that it only contains one entry per isotopologue, and that
# entry contains a state ID. The fields read in on each line are iso_id,
# (iso_name), zpe_state_id, (s_qns), though the 2nd and 4th fields aren't used.

SETTINGS_PATH = '/Users/christian/research/VAMDC/HITRAN/django/HITRAN'
# Django needs to know where to find the HITRAN project's settings.py:
sys.path.append(SETTINGS_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Iso
from hitranlbl.models import State

for line in open('ZPE_state_ids.txt', 'r'):
    fields = line.split()
    iso_id = int(fields[0])
    zpe_state_id = int(fields[2])
    iso = Iso.objects.filter(pk=iso_id).get()
    iso.ZPE_state_id = zpe_state_id
    print '%d.%s ZPE_state_id = %d' % (iso_id, iso.iso_name, zpe_state_id)
    iso.save()
    

