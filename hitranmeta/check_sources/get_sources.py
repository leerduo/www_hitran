#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cp_source.py

import os
import sys

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from hitranmeta.models import Molecule, Iso
from hitranlbl.models import Trans, Prm
from hitranmeta.models import Ref, Source, SourceType, SourceMethod

ref_pos = {'nu': 133, 'Sw': 135, 'gamma_air': 137, 'gamma_self': 139,
           'n_air': 141, 'delta_air': 143}

molec_name = 'H2O'
prm_name = 'delta_air'

html_name = '%s_%s.html' % (molec_name, prm_name)
fo = open(html_name, 'w')
print >>fo, '<html><head>'
print >>fo, '<link rel="stylesheet" href="sources.css" type="text/css" media="screen"/>'
print >>fo, '<link rel="stylesheet" href="sources_print.css" type="text/css" media="print"/>'
print >>fo, '<meta charset="utf-8"/>'
print >>fo, '</head><body>'

molecule = Molecule.objects.filter(ordinary_formula=molec_name).get()
isotopologues = Iso.objects.filter(molecule=molecule)
transitions = Trans.objects.filter(iso__in=isotopologues).select_related()

source_ids = {}
for trans in transitions:
    refID = int(trans.par_line[ref_pos[prm_name]:ref_pos[prm_name]+2])
    #prm = Prm.objects.filter(name=prm_name).get(trans=trans)
    try:
        prm = trans.prm_set.filter(name=prm_name).get()
    except Prm.DoesNotExist:
        if (prm_name == 'delta_air' and refID == 0)\
                or trans.par_line[59:67] == '0.000000':
            continue
        else:
            print 'couldn\'t find refID=%d in sources for %s-%s'\
                % (refID, molec_name, prm_name)
    source_id = prm.source.id
    if refID not in source_ids.keys():
        source_ids[refID] = source_id
    else:
        if source_ids[refID] != source_id:
            print 'oops'
            sys.exit(1)

print >>fo, '<ol>'
for refID in sorted(source_ids.keys()):
    source_id = source_ids[refID]
    source = Source.objects.get(pk=source_id)
    print >>fo, '<li>%s: %s</li>' % (unicode(refID).encode('utf-8'),
                unicode(source.html(sublist=True)).encode('utf-8'))
print >>fo, '</ol>'
print >>fo, '</body></html>'
fo.close()
    
sys.exit(0)




prms = Prm.objects.filter(trans__in=transitions).filter(name='Sw').select_related('source')
sources = {}
for prm in prms:
    source = prm.source
    try:
        ref_source = Source.objects.get(pk=prm.ref.source_id)
    except Source.DoesNotExist:
        print 'couldn\'t find source with id', prm.ref.source_id,\
              ' for which refID =',prm.ref.refID
        continue
    if source != ref_source:
        print 'source/ref_source mismatch'
    sources[prm.ref.refID] = source
print '<ol>'
for refID, source in sources.items():
#for source in sources:
    if source is None:
        continue
    #print '<li>%s</li>' % unicode(source.html(sublist=True)).encode('utf-8')
    print '<li>%s: %s</li>' % (unicode(refID).encode('utf-8'), unicode(source.html(sublist=True)).encode('utf-8'))
print '</ol>'

print '</body></html>'

#    if source.source_list:
#        for source2 in source.source_list.all():
#            print source.id, ':', ', '.join(str(source2.id))
#    else:
#        print source.id,'::',
#
