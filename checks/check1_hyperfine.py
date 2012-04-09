#!/usr/bin/env python
# check1_hyperfine.py

import os
import sys
HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Molecule, Iso, NucSpins
from hitranlbl.models import State

molec_name = sys.argv[1]
isoID = int(sys.argv[2])

molecule = Molecule.objects.filter(ordinary_formula=molec_name).get()
iso = Iso.objects.filter(molecule=molecule).filter(isoID=isoID).get()
try:
    nucspins = NucSpins.objects.filter(iso=iso).get()
except NucSpins.DoesNotExist:
    print 'No known nuclear spins for', iso.iso_name
    sys.exit(0)
I = nucspins.I
print '%s: I(%s) = %.1f' % (iso.iso_name, nucspins.atom_label, nucspins.I)

states = State.objects.filter(iso=iso).filter(s_qns__contains='F#')
print states.count(),'states with hyperfine quantum number F found.'

s_Fqn = 'F#nuclearSpinRef:%s' % nucspins.atom_label
nbad = 0
for state in states:
    s_qns = state.s_qns.split(';')
    qn_dict = {}
    for s_qn in s_qns:
        qn_name, qn_val = s_qn.split('=')
        qn_dict[qn_name] = qn_val
    F = float(qn_dict[s_Fqn])
    try:
        J = float(qn_dict['J'])
    except KeyError:
        print 'no J quantum number for this state'
        continue
    #print 'J =',J,'; F =', F, 'for I =',I
    if F < abs(J-I) or F > J+I:
        print 'Bad hyperfine or J quantum number for stateID=%d:'\
              ' F=%.1f, J=%.1f' % (state.id, F, J)
        nbad +=1

print nbad,'bad states found.'

