#!/usr/bin/env python
# cp_source.py

import os
import sys

HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME, 'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from models import Ref, Source, SourceType, SourceMethod

refID = sys.argv[1]
s_method = sys.argv[2]
try:
    source_method_id = int(s_method)
    source_method = SourceMethod.objects.get(pk=source_method_id)
except ValueError:
    try:
        source_method = SourceMethod.objects.get(method_name=s_method)
    except SourceMethod.DoesNotExist:
        print 'bad method:', s_method
        sys.exit(1)
except SourceMethod.DoesNotExist:
    print 'bad method id:', s_method
    sys.exit(1)

try:
    ref = Ref.objects.get(refID=refID)
except Ref.DoesNotExist:
    print refID,'does not exist in Ref table!'
    sys.exit(1)
print ref.refID, ref.title

try:
    source_type = SourceType.objects.get(source_type=ref.ref_type)
except SourceType.DoesNotExist:
    print ref.ref_type,'does not exist in SourceType table!'
    sys.exit(1)

source = Source(refID=refID, source_type=source_type, authors=ref.authors,
                title=ref.title, title_html=ref.title_html, journal=ref.journal,
                volume=ref.volume, page_start=ref.page_start,
                page_end=ref.page_end, year=ref.year, institution=ref.institution,
                note=ref.note, note_html=ref.note_html, doi=ref.doi,
                cited_as_html=ref.cited_as_html, url=ref.url,
                method=source_method)
source.save()
