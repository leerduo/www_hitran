#!/usr/bin/env python
# check3_JK.py

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
    states = State.objects.filter(iso=iso).filter(s_qns__contains='J=')
    for state in states:
        s_qns = state.s_qns.split(';')
        qn_dict = {}
        for s_qn in s_qns:
            qn_name, qn_val = s_qn.split('=')
            qn_dict[qn_name] = qn_val
        J = float(qn_dict['J'])
        try:
            K = float(qn_dict['K'])
        except KeyError:
            continue
        if J < K:
            print 'J = %s but K = %s for stateID = %d' % (
                qn_dict['J'], qn_dict['K'], state.id)
            nbad +=1
    print nbad,'bad states found for %s.' % iso.iso_name

