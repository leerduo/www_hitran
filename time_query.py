#!/usr/bin/env python
# -*- coding: utf-8 -*-
# time_query.py

# Christian Hill, 1/9/11
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
# Django needs to know where to find the HITRAN project's settings.py:

import os
import sys
HOME = os.getenv('HOME')
hitran_path = os.path.join(HOME,'research/VAMDC/HITRAN/django/HITRAN')
sys.path.append(hitran_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
from hitranlbl.models import *
from django.db.models import Q
from hitranmeta.models import Molecule, OutputCollection, Iso
from hitranlbl.lbl_searchform import LblSearchForm
from hitranlbl import views

# Limit the number of returned transitions to TRANSLIM, if not None:
TRANSLIM = None

class FormData(object):
    def __init__(self, output_collection, date, get_states, molecule):
        self.dic = {}
        self.dic['numin'] = ''
        self.dic['numax'] = ''
        self.dic['numin_units'] = 'cm-1'
        self.dic['Swmin'] = ''
        self.dic['output_collection'] = output_collection
        self.dic['date'] = date
        self.dic['get_states'] = get_states
        self.molecule = molecule
    def get(self, name):
        return self.dic[name]
    def getlist(self, name):
        return self.molecule

post_data = FormData(2, '2011-09-01', True, [2,3,])
form = LblSearchForm(post_data)

output_files, search_summary = views.do_search(form)
print output_files
print search_summary
