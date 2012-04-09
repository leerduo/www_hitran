#!/usr/bin/env python
# check4_JKaKc.py

import os
import sys
HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Molecule, Iso
from hitranlbl.models import State

if len(sys.argv) > 1:
    molec_name = sys.argv[1]
    isoID = int(sys.argv[2])
    molecule = Molecule.objects.filter(ordinary_formula=molec_name).get()
    isos = Iso.objects.filter(molecule=molecule).filter(isoID=isoID)
else:
    isos = Iso.objects.all()

for iso in isos:
    print iso.iso_name
    nbad = 0
    states = State.objects.filter(iso=iso).all()
    for state in states:
        s_qns = state.s_qns.split(';')
        qn_dict = {}
        for s_qn in s_qns:
            qn_name, qn_val = s_qn.split('=')
            qn_dict[qn_name] = qn_val
        try:
            JN = int(qn_dict['N'])
            s_JN = 'N'
        except KeyError:
            # no N quantum number, try J
            try:
                JN = int(qn_dict['J'])
                s_JN = 'J'
            except (KeyError, ValueError):
                # J doesn't exist or is non-integer
                continue
        try:
            Ka = int(qn_dict['Ka'])
            Kc = int(qn_dict['Kc'])
        except KeyError:
            continue
        if JN < Ka:
            print '%s = %d < Ka = %d for stateID = %d' % (
                s_JN, JN, Ka, state.id)
        if JN < Kc:
            print '%s = %d < Kc = %d for stateID = %d' % (
                s_JN, JN, Kc, state.id)
        if Ka+Kc not in (JN, JN+1):
            print 'Ka+Kc != %s or %s+1: %s = %d, Ka = %d, Kc = %d for'\
                  ' stateID = %d' % (s_JN, s_JN, s_JN, JN, Ka, Kc, state.id)
            nbad +=1
    print nbad,'bad states found for %s.' % iso.iso_name


