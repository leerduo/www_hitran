#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cp_source.py

import os
import sys

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from models import Ref, Source, SourceType, SourceMethod

def source_to_html(source):
    if source.source_type.source_type == 'article':
        s = '%s, "%s", <em>%s</em> <strong>%s</strong>, %s-%s (%d)'\
                % (source.authors, source.title, source.journal,
                   source.page_start, source.page_end, source.year)
        return s
    return 'uncoded'


print '<html><head><meta charset="utf-8"/></head><body>'
sources = Source.objects.all()
print '<ol>'
for source in sources:
    print '<li>%s</li>' % unicode(source.html()).encode('utf-8')
print '</ol>'

print '</body></html>'

#    if source.source_list:
#        for source2 in source.source_list.all():
#            print source.id, ':', ', '.join(str(source2.id))
#    else:
#        print source.id,'::',
#
