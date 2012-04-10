#!/usr/bin/env python
# -*- coding: utf-8 -*-
# load_Q.py

# Christian Hill, 9/11/11
# Parse and load up the HITRAN partition function data to the hitran relational
# database and results/Q directory

import os
import sys
import datetime
import xn_utils

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
Q_path = os.path.join(HOME, 'research/HITRAN/HITRAN2008/Global_Data/parsum.dat')
sys.path.append(Q_path)
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from models import Molecule
from models import Iso
from models import PartitionFunction

mod_date = datetime.date.fromtimestamp(os.path.getmtime(Q_path)).isoformat()

fi = open(Q_path, 'r')
header = fi.readline()
isos = []
for field in header.split()[1:]:
    field = field.strip()
    molec_name, afgl_code = field.split('_')
    # CO2 alternative AFGL code
    if afgl_code == '827': afgl_code = '728'
    # these isotopologues of O3 don't have lines in HITRAN
    if afgl_code in ('678', '767', '768', '776', '777', '778', '786', '787',
                     '868', '878', '886', '887', '888'):
        isos.append(None)
        continue
    if field in ('SF6_29', 'ClONO2_5646', 'ClONO2_7646'):
        isos.append(None)
        continue
    molecule = Molecule.objects.filter(ordinary_formula=molec_name).get()
    isos.append(Iso.objects.filter(molecule=molecule).filter(afgl_code=afgl_code).get())
for iso in isos:
    if iso is not None:
        iso.Q = []

T = []
for line in fi.readlines():
    fields = line.split()
    T.append(float(fields[0]))
    for i, iso in enumerate(isos):
        if iso is None:
            continue
        iso.Q.append(fields[i+1])
n=len(T)

if True:
    for iso in isos:
        if iso is None:
            continue
        q_name = '%s_%d.q' % (iso.molecule.ordinary_formula, iso.isoID)
        q = PartitionFunction(iso=iso, n=n, Tmin = T[0], Tmax = T[-1], dT = 1.,
                              valid_from=mod_date, filename=q_name)
        q.save()

if True:
    # write partition function files for each isotopologue
    for iso in isos:
        if iso is None:
            continue
        filestem = '%s_%d' % (iso.molecule.ordinary_formula, iso.isoID)
        # the two-column (T, Q) .pfn file:
        pfn_name = '%s.pfn' % filestem
        pfn_path = os.path.join(hitran_path, 'results/Q', pfn_name)
        pfn_o = open(pfn_path, 'w')
        q_name = '%s.q' % filestem
        q_path = os.path.join(hitran_path, 'results/Q', q_name)
        q_o = open(q_path, 'w')
        for i, Q in enumerate(iso.Q):
            print >>pfn_o, '%6.1f %s' % (T[i], Q)
            print >>q_o, Q
        pfn_o.close()
        q_o.close()

