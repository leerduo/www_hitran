#!/usr/bin/env python
# iso_table.py
# Christian Hill
# Create an HTML page with a table of the HITRAN isotopologues

import os
import sys
HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from hitranmeta.models import Molecule, Iso, NucSpins

fo = open('isos.html', 'w')
print >>fo, '<html><head>'
print >>fo, '<style type="text/css">'
print >>fo, 'tr.pb > td {padding-bottom: 20px;}'
print >>fo, '</style>'
print >>fo, '</head><body>'
molecules = Molecule.objects.all().order_by('molecID')
print >>fo, '<table>'
for molecule in molecules:
    if molecule.molecID >= 100:
        break
    isos = Iso.objects.filter(molecule=molecule).order_by('isoID')
    niso = isos.count()
    scls = ''
    if niso == 1:
        scls = ' class="pb"'
    print >>fo, '<tr%s><td rowspan="%d">%d</td><td rowspan="%d">%s</td>'\
        % (scls, niso, molecule.molecID, niso, molecule.ordinary_formula_html)
    for i,iso in enumerate(isos):
        if i > 0:
            if i == niso-1:
                scls = ' class="pb"'
            print >>fo, '<tr %s>' % scls,
        print >>fo, '<td>%d<td><td>%s</td><td>%d</td><td><tt>%s</tt><td>'\
                    '<td><tt>%s</tt></td><td><tt>%s</tt></td></tr>'\
                  % (iso.isoID, iso.iso_name_html, iso.id, iso.iso_name,
                     iso.abundance, '') #iso.InChIKey)
print >>fo, '</table>'
print >>fo, '</body></html>'
fo.close()


