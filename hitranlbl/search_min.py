# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from search_utils import make_simple_sql_query, get_filestem, hitranIDs

def do_search_min(form):
    """
    A search involving return of a fairly minimal set of parameters from the
    hitranlbl_trans table only, with no joins required.

    """

    start_time = time.time()
    query_fields = ['iso_id', 'nu', 'A', 'Elower', 'gp', 'gpp']
    query = make_simple_sql_query(form, query_fields)

    search_summary = {'summary_html':
            '<p>Here are the results of the query in "min" format.'\
            ' Note that no data sources are output in this format</p>'}

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    ntrans = len(rows)
    te = time.time()
    print 'time to get %d transitions = %.1f secs' % (ntrans, (te-start_time))

    ts = time.time()
    filestem = get_filestem()
    output_files = write_min(filestem, rows, form)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_min(filestem, rows, form):
    """
    Write the output transitions file for the "min" output collection.
    The rows returned from the database query are:
    iso_id, nu, Sw, Elower, gp

    """

    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(outpath, 'w')

    s_fmt = form.field_separator.join(
            ['%2d','%2d','%12.6f','%10.3e','%10s','%5s','%5s'])

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_g = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_g = form.default_entry * 5

    for row in rows:
        iso_id = row[0]
        molecule_id, local_iso_id = hitranIDs[iso_id]
        try:
            s_Epp = '%10.4f' % row[3]
        except TypeError:
            s_Epp = default_Epp
        try:
            s_gp = '%5d' % row[4]
        except TypeError:
            s_gp = default_g
        try:
            s_gpp = '%5d' % row[4]
        except TypeError:
            s_gpp = default_g

        print >>fo, s_fmt % (
                    molecule_id,
                    local_iso_id,
                    row[1], # nu
                    row[2], # A
                    s_Epp,
                    s_gp, s_gpp)
            
    fo.close()
    return [outpath,]

