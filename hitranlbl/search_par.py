# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from search_utils import make_simple_sql_query, get_filestem, get_refIDs,\
                         write_refs

def do_search_par(form):
    """
    Do the search as a raw SQL query, returning the native HITRAN2004+ 160-
    byte format.

    """

    start_time = time.time()

    query = make_simple_sql_query(form, ['par_line',])

    search_summary = {'summary_html':
                '<p>Here are the results of the query in native'\
                ' 160-byte HITRAN2004+ format</p>'}

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    par_lines = cursor.fetchall()

    ntrans = len(par_lines)
    te = time.time()
    print 'time to get %d transitions = %.1f secs' % (ntrans, (te-start_time))

    ts = time.time()
    filestem = get_filestem()
    output_file_list = write_par(filestem, par_lines)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    if form.output_sources:
        # to output sources by source_id:
        refIDs = get_refIDs(par_lines)
        ref_files = write_refs(form, filestem, refIDs)
        output_file_list.extend(ref_files)

    # strip path from output filenames:
    output_file_list = [os.path.basename(x) for x in output_file_list]

    return output_file_list, search_summary

def write_par(filestem, par_lines):
    parpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(parpath, 'w')
    # the rows from the SQL query come back as tuples with the single
    # element par_line, so we need an index here
    for par_line in par_lines:
        print >>fo, par_line[0]
    fo.close()
    return [parpath,]

