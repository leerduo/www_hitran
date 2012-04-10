# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from models import *
from django.db.models import Q
from hitranmeta.models import Molecule, OutputCollection, Iso, Ref
from lbl_searchform import LblSearchForm
import os
import time
import datetime
from itertools import chain

# get a list of molecule objects with entries in the Trans table
p_ids = Trans.objects.values('iso__molecule').distinct()
present_molecules = Molecule.objects.filter(molecID__in=p_ids)

output_collections = OutputCollection.objects.all()

def index(request):
    if request.POST:
        form = LblSearchForm(request.POST)
        form_valid, msg = form.is_valid()
        if form_valid:
            output_files, search_summary = do_search(form)
            c = {'search_summary': search_summary,
                 'output_files': output_files}
        else:
            c = {'search_summary': {'summary_html': '<p>There were errors in'
                ' your search parameters:</p>%s' % msg}}
        return render_to_response('lbl_searchresults.html', c)

    c = {}
    c.update(csrf(request))
    c['present_molecules'] = present_molecules
    c['output_collections'] = output_collections
    return  render_to_response('index.html', c)

def do_search(form):
    """
    Do the search, using the search parameters parsed in the form instance
    of the LblSearchForm class.

    """

    start_time = time.time()

    search_summary = {'summary_html': '<p>Success!</p>'}
    isos = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)
    # TODO detect when all isotopologues have been selected and ditch this
    # filter in that case:
    query = Q(iso__in=isos)
    if form.numin:
        query = query & Q(nu__gte=form.numin)
    if form.numax:
        query = query & Q(nu__lte=form.numax)
    if form.Swmin:
        query = query & Q(Sw__gte=form.Swmin)
    #query = query & Q(valid_from__lte=form.datestamp)
    #query = query & Q(valid_to__gte=form.datestamp)

    print 'query =',query

    #transitions = Trans.objects.filter(query).select_related().order_by('nu')
    #transitions = Trans.objects.filter(query).select_related('hitranlbl_prm')
    #ntrans = transitions.count()
    par_lines = Trans.objects.filter(query).values_list('par_line', flat=True)
    ntrans = len(par_lines)
    te = time.time()
    print 'time to get transitions = %.1f secs' % (te-start_time)

    if settings.TIMED_FILENAMES:
        # integer timestamp: the number of seconds since 00:00 1 January 1970
        ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    else:
        # otherwise use a fixed timestamp for generating the filename
        ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]

    

    output_files = write_par(filestem, par_lines)



    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    #search_summary['ntrans'] = len(transitions)
    search_summary['ntrans'] = len(par_lines)
    #search_summary['percent_returned'] = '%.1f' % percent_returned
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_par(filestem, par_lines):
    parpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(parpath, 'w')
    for par_line in par_lines:
        print >>fo, par_line
    fo.close()
    return [parpath,]
    
