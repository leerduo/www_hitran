#!/usr/bin/env python
# -*- coding: utf-8 -*-
# load_xsc_data.py

# Christian Hill, 28/10/11
# Load up metadata to the hitranxsc_xsc table and place the corresponding
# text table files in the results/xsc directory

import os
import sys
import glob
import datetime
import xn_utils

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
ir_xsc_path = os.path.join(HOME, 'research/HITRAN/HITRAN2008/IR-XSect/'\
                                 'Uncompressed-files')
uv_xsc_path = os.path.join(HOME, 'research/HITRAN/HITRAN2008/UV/'\
                                 'Cross-sections')
#sys.path.append(xsc_path)
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import MoleculeName
from models import Xsc

xscresults_path = os.path.join(hitran_path, 'results/xsc')

# alternative names used in the cross sections file headers for some molecules,
# but which we don't actually want to put in the molecule_names database:
alt_names = {
'chlorinedioxide': 'Chlorine dioxide',
'nitrogentrioxid': 'Nitrate radical',
'oxylene': 'o-xylene',
'mxylene': 'm-xylene',
'pxylene': 'p-xylene',
'C7H8': 'toluene',
}

try:
    molec_name = sys.argv[1]
    iruv = sys.argv[2].upper()
    if iruv == 'UV':
        ir = False
    elif iruv == 'IR':
        ir = True
    else:
        raise
except:
    print 'usage is:'
    print '%s <molec_name> <IR|UV>' % sys.argv[0]
    sys.exit(1)

# the name of the molecule in the native HITRAN filenames
molec_filename = molec_name
# the name of the molecule in my moleculename database
if molec_name in alt_names:
    molec_name = alt_names[molec_name]
try:
    molec_id = MoleculeName.objects.filter(name=molec_name).get().molecule_id
except MoleculeName.DoesNotExist:
    print 'Molecule name %s not found.' % molec_name
    sys.exit(1)

print molec_name,'has ID', molec_id

filenames = []
# cross section filenames must be '<molec_name>_???.xsc' where ??? can be
# anything.
if ir:
    glob_paths = [os.path.join(ir_xsc_path,'%s_*.xsc' % molec_filename),]
else:
    # some UV cross section files use the '-' separator instead of '_'
    glob_paths = [os.path.join(uv_xsc_path,'%s_*.xsc' % molec_filename),
                  os.path.join(uv_xsc_path,'%s-*.xsc' % molec_filename)]
for glob_path in glob_paths:
    filenames.extend(glob.glob(glob_path))
if len(filenames)==0:
    print 'no files matching pattern:\n%s' % '\n'.join(glob_paths)
    sys.exit(1)
for filename in filenames:
    print filename
    mod_date = datetime.date.fromtimestamp(os.path.getmtime(
                    filename)).isoformat()
    print mod_date
    year_digits = mod_date[2:4]
    fi = open(filename, 'r')
    while fi:
        header = fi.readline()
        xsc = Xsc.parse_meta(molec_id, header)
        if not xsc:
            break
        print 'T =',xsc.T,'; p =',xsc.p
        nlines = xsc.n / 10
        if xsc.n % 10:
            nlines += 1
        xsc.valid_from = mod_date

        filestem =  '%s_%.1fK-%.1fTorr_%.1f-%.1f_%s' % (molec_name,
                            xsc.T, xsc.p, int(round(xsc.numin)),
                            int(round(xsc.numax)), year_digits)
        xsc.filename = '%s.xsc' % filestem
        print filestem
        xsc_name = os.path.join(xscresults_path, xsc.filename)
        xsc_out = open(xsc_name, 'w')
        print >>xsc_out, header.strip()
        
        i = 0
        npts = 0
        s_sigma = []
        while i<nlines:
            i += 1
            line = fi.readline().strip()
            print >>xsc_out, line
            chunk = line.split()
            s_sigma.extend(chunk)
            npts += len(chunk)
        print npts, xsc.n
        xsc_out.close()
        if npts < xsc.n:
            print 'fatal: npts read in < xsc.n'
            sys.exit(1)
        if npts > xsc.n:
            # for some data files the cross section is padded with zeroes
            # on the last line.
            print 'npts read in > xsc.n'
            for pt in s_sigma[npts-1:]:
                if pt != '0.000E+00':
                    print 'non-zero data beyond n =', xsc.n
            s_sigma = s_sigma[:xsc.n]


        sigma_name = os.path.join(xscresults_path, '%s.sigma' % filestem)
        xn_utils.write_list(sigma_name, s_sigma)
        xsc.save()
    fi.close()


