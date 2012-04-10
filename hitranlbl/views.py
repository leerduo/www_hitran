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

    print 'form.output_collection_index = ',form.output_collection_index
    output_collection = output_collections[form.output_collection_index]
    print 'output_collection =',output_collection.name 

    if output_collection.name == 'HITRAN2004+':
        return do_search_par(form)
    print 'unknown collection!'
    return None

def do_search_par(form):
    """
    Do the search as a raw SQL query, returning the native HITRAN2004+ 160-
    byte format.

    """

    start_time = time.time()

    search_summary = {'summary_html':
                '<p>Here are the results of the query in native'\
                ' 160-byte HITRAN2004+ format</p>'}
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)
    q_numin = ''
    if form.numin:
        q_numin = ' AND nu>=%f' % form.numin
    q_numax = ''
    if form.numax:
        q_numax = ' AND nu<=%f' % form.numax
    q_Swmin = ''
    if form.Swmin:
        q_Swmin = ' AND Sw>=%e' % form.Swmin

    query = 'SELECT par_line FROM hitranlbl_trans WHERE iso_id'\
            ' IN (%s)%s%s%s' % (iso_ids_list, q_numin, q_numax, q_Swmin)
    #print query

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    par_lines = cursor.fetchall()

    ntrans = len(par_lines)
    te = time.time()
    print 'time to get transitions = %.1f secs' % (te - start_time)

    if settings.TIMED_FILENAMES:
        # integer timestamp: the number of seconds since 00:00 1 January 1970
        ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    else:
        # otherwise use a fixed timestamp for generating the filename
        ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]

    ts = time.time()
    output_files = write_par(filestem, par_lines)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_par(filestem, par_lines):
    parpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(parpath, 'w')
    # the rows from the SQL query come back as tuples with the single
    # element par_line, so we need an index here
    for par_line in par_lines:
        print >>fo, par_line[0]
    fo.close()
    return [parpath,]
    
