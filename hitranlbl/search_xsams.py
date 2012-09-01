# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from hitranmeta.models import Iso

def do_search_xsams(form):
    isos = Iso.objects.filter(pk__in=form.selected_isoIDs)
    
    iso_inchikeys = ','.join([iso.InChIKey for iso in isos])

    # isotopologues
    q_conds = ['InChIKey IN (%s)' % iso_inchikeys,]

    # wavenumber range
    if form.numin:
        q_conds.append('RadTransWavenumber >= %f' % form.numin)
    if form.numax:
        q_conds.append('RadTransWavenumber <= %f' % form.numax)

    # TODO threshold condition on Sw

    # threshold condition on Einstein A-coefficient
    if form.Amin:
        q_conds.append('RadTransProbabilityA >= %e' % form.Amin)
    
    vss2_query = 'SELECT * WHERE %s' % ' AND '.join(q_conds)

    hitran_node_url = 'http://vamdc.mssl.ucl.ac.uk/node/hitran/tap/sync/'\
                      '?REQUEST=doQuery&LANG=VSS2&FORMAT=XSAMS&QUERY=%s'\
                            % vss2_query
    
    
