#!/usr/bin/env python
# check5_g.py

import os
import sys
HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Molecule, Iso, NucSpins
from hitranlbl.models import State
from g_ns import g_ns

molec_name = sys.argv[1]
isoID = int(sys.argv[2])
molecule = Molecule.objects.filter(ordinary_formula=molec_name).get()
iso = Iso.objects.filter(molecule=molecule).filter(isoID=isoID).get()
print iso.iso_name
I = None
try:
    nucspins = NucSpins.objects.filter(iso=iso).get()
    I = nucspins.I
    print '%s: I(%s) = %.1f' % (iso.iso_name, nucspins.atom_label, nucspins.I)
    s_Fqn = 'F#nuclearSpinRef:%s' % nucspins.atom_label
except NucSpins.DoesNotExist:
    print 'No known resolved hyperfine structure for', iso.iso_name
states = State.objects.filter(iso=iso).all()
nstates = states.count()

nbad = 0
nndef = 0
ngood = 0
for state in states:
    s_qns = state.s_qns.split(';')
    qn_dict = {}
    for s_qn in s_qns:
        qn_name, qn_val = s_qn.split('=')
        qn_dict[qn_name] = qn_val
    g = g_ns(iso, qn_dict)
    if g is None:
        nndef += 1
        continue

    F = None
    if I:
        try:
            F = float(qn_dict[s_Fqn])
        except KeyError:
            pass
    if F is None:
        try:
            J = float(qn_dict['J'])
            g *= int(round(2. * J + 1.))
        except KeyError:
            continue
    else:
        g *= 2. * F + 1.
        g /= 2. * I + 1.
        g = int(round(g))

    # Electronic states with |Lambda| > 0 come in +/- parity pairs
    try:
        Lambda = qn_dict['Lambda']
        if Lambda > 0:
            parity = qn_dict.get('parity')
            if not parity:
                # unresolved Lambda-doubling
                g *= 2
    except KeyError:
        pass

    if state.g != g:
        print 'bad degeneracy for state',state.id,': state.g =', state.g,\
            ' should be', g
        print state.s_qns
        nbad += 1
    else:
        ngood += 1
title = '%s summary' % iso.iso_name
print title; print '-' * len(title)
print '%d/%d good degeneracies' % (ngood, nstates)
print '%d/%d bad degeneracies' % (nbad, nstates)
print '%d/%d undetermined degeneracies' % (nndef, nstates)
