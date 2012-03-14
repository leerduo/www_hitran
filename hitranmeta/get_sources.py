#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cp_source.py

import os
import sys

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from models import Molecule, Iso
from hitranlbl.models import Trans, Prm
from models import Ref, Source, SourceType, SourceMethod

def source_to_html(source):
    if source.source_type.source_type == 'article':
        s = '%s, "%s", <em>%s</em> <strong>%s</strong>, %s-%s (%d)'\
                % (source.authors, source.title, source.journal,
                   source.page_start, source.page_end, source.year)
        return s
    return 'uncoded'


print '<html><head>'
print '<link rel="stylesheet" href="sources.css" type="text/css" media="screen"/>'
print '<meta charset="utf-8"/>'
print '</head><body>'
#sources = Source.objects.all()
#sources = Source.objects.filter(refID__startswith="NOp-nu")
molecule = Molecule.objects.filter(ordinary_formula="NO+").get()
isotopologues = Iso.objects.filter(molecule=molecule)
transitions = Trans.objects.filter(iso__in=isotopologues)
prms = Prm.objects.filter(trans__in=transitions).select_related('source')
sources = set([prm.source for prm in prms])
print '<ol>'
for source in sources:
    if source is None:
        continue
    #print '<li>%s</li>' % unicode(source.html(sublist=True)).encode('utf-8')
    print '<li>%s: %s</li>' % (unicode(source.refID).encode('utf-8'), unicode(source.html(sublist=True)).encode('utf-8'))
print '</ol>'

print '</body></html>'

#    if source.source_list:
#        for source2 in source.source_list.all():
#            print source.id, ':', ', '.join(str(source2.id))
#    else:
#        print source.id,'::',
#
