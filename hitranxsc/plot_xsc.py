#!/usr/bin/env python
# -*- coding: utf-8 -*-
# plot_xsc.py

# Christian Hill, 1/11/11
# Plot cross section data matching some query.

import os
import sys
import glob
import datetime
import xn_utils
import pylab

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
xsc_path = os.path.join(HOME, 'research/HITRAN/HITRAN2008/IR-XSect/'\
                              'Uncompressed-files')
sys.path.append(xsc_path)
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
from hitranmeta.models import Molecule, MoleculeName
from models import Xsc
from django.db.models import Q

selected_molecIDs=[114,]
numin = 720.; numax = 1000.
Tmin = 200.; Tmax = 300.
pmin = pmax = None

molecules = Molecule.objects.filter(pk__in=selected_molecIDs)
query = Q(molecule__in=molecules)
if numin:
    query = query & Q(numax__gte=numin)
if numax:
    query = query & Q(numin__lte=numax)
if Tmin:
    query = query & Q(T__gte=Tmin)
if Tmax:
    query = query & Q(T__lte=Tmax)
if pmin:
    query = query & Q(p__gte=pmin)
if pmax:
    query = query & Q(p__lte=pmax)
#query = query & Q(valid_from__lte=datestamp)
#query = query & Q(valid_to__gte=datestamp)
xscs = Xsc.objects.filter(query)

class Plot(object):
    def __init__(self, xsc):
        self.numin, self.numax, self.n = xsc.numin, xsc.numax, xsc.n
        self.dnu = (self.numax - self.numin) / (self.n - 1)
        self.xgrid = [self.numin + i*self.dnu for i in range(self.n)]
        self.sigma_name = xsc.filename.replace('xsc', 'sigma')
        self.filepath = os.path.join(settings.RESULTSPATH, 'xsc',
            self.sigma_name)
        self.read_xsc()
    def read_xsc(self):
        self.ygrid = [float(s_y) for s_y in open(self.filepath, 'r')]

plots = []
for xsc in xscs:
    plots.append(Plot(xsc))
for plot in plots:
    pylab.plot(plot.xgrid, plot.ygrid)
pylab.show()

