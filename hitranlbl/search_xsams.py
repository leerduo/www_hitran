# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from django.db import connection
from hitranmeta.models import Iso, Source
from search_utils import get_basic_conditions, get_filestem, get_iso_ids_list,\
                         get_all_source_ids
from xsams_generators import xsams_preamble, xsams_sources, xsams_close,\
                             xsams_functions, xsams_environments,\
                             xsams_species_with_states

prm_names = ['nu', 'Sw', 'A', 'gamma_air', 'gamma_self', 'n_air', 'delta_air']
def get_src_ids(q_subwhere):
    """
    Get a list of distinct source IDs for the parameters returned by the
    search.

    Arguments:
    q_subwhere: a string of SQL comprising the basic conditions on the
    transitions table query.

    Returns:
    src_ids: a list of distinct primary keys to the Sources referenced by
    the parameters to be returned by the query.

    """

    print 'Fetching sources...'
    st = time.time()

    sub_queries = []
    limit_query = ''
    if settings.LIMIT is not None:
        limit_query = ' LIMIT %d' % settings.LIMIT
    for prm_name in prm_names:
        if prm_name == 'A':
            # the source for A is always the same as that for Sw, so skip
            continue
        sub_queries.append(
                'SELECT DISTINCT(p_%s.source_id) AS src_id'
                ' FROM hitranlbl_trans t, prm_%s p_%s WHERE %s AND'
                ' p_%s.trans_id=t.id%s' % (prm_name, prm_name, prm_name,
                                           q_subwhere, prm_name, limit_query)
                          )
    src_query = ['SELECT DISTINCT(src_id) FROM (',]
    src_query.append(' UNION '.join(sub_queries))
    src_query.append(') x')  # "Every derived table must have its own alias"
    src_query = ''.join(src_query)
    print src_query

    cursor = connection.cursor()
    cursor.execute(src_query)
    rows = cursor.fetchall()
    src_ids = [row[0] for row in rows]  # rows is a tuple of tuples: (src_id,)
    src_ids.sort()

    et = time.time()
    print '%d sources found in %.1f secs' % (len(src_ids), et-st)
    return src_ids

def get_states_rows(q_subwhere):
    """
    Get the states involved in the transitions selected by the query,
    ordered by their (global) isotopologue IDs.

    """

    print 'Fetching states...'
    st = time.time()

    limit_query = ''
    if settings.LIMIT is not None:
        limit_query = ' LIMIT %d' % settings.LIMIT
    sub_queryp = 'SELECT DISTINCT(statep_id) AS sid FROM hitranlbl_trans t'\
                 ' WHERE %s' % q_subwhere
    sub_querypp = 'SELECT DISTINCT(statepp_id) AS sid FROM hitranlbl_trans t'\
                 ' WHERE %s' % q_subwhere
    
    st_query = 'SELECT st.iso_id, st.id, st.energy, st.g, st.nucspin_label,'\
          ' st.qns_xml FROM hitranlbl_state st, (SELECT DISTINCT(sid)'\
          ' FROM (%s UNION %s) sids, hitranlbl_state s WHERE sids.sid=s.id)'\
          ' qst WHERE st.id=sid ORDER BY st.iso_id' % (sub_queryp, sub_querypp)
    print st_query
    
    cursor = connection.cursor()
    cursor.execute(st_query)

    et = time.time()
    print 'states retrieved in %.1f secs' % (et - st)
    return cursor.fetchall()

def do_search_xsams(form):
    """
    Search the database for the requested transitions, and return them in
    XSAMS format.

    Arguments:
    form: the Django-parsed Form object containing the parameters for the
    search.

    Returns:
    output_file_list: a list of the names of files written to produce the
    results of this search, stripped of any path information (ie basename
    only; the files are assumed to have been put in the RESULTSPATH directory.

    search_summary: a dictionary of stuff to pass to the search results
    template, including search_summary - a text description of the format
    the data is returned in.

    """
    start_time = time.time()

    filestem = get_filestem()
    outpath = os.path.join(settings.RESULTSPATH, '%s.xsams' % filestem)
    output_files = [outpath,]

    fo = open(outpath, 'w')

    # get a comma-separated string comprising a list of the ids of the
    # requested isotopologues
    iso_ids_list = get_iso_ids_list(form)

    # the basic constraints of the query on the transitions table
    q_conds = ['t.%s' % q_cond for q_cond in get_basic_conditions(
                                            iso_ids_list, form)]
    q_subwhere = ' AND '.join(q_conds)

    write_xsams(fo, xsams_preamble, timestamp=start_time)

    # Sources
    source_ids = get_src_ids(q_subwhere)
    # we need all the source_ids, even those belonging to sources cited
    # within notes, etc.
    all_source_ids = get_all_source_ids(source_ids)
    all_sources = Source.objects.filter(pk__in=all_source_ids)
    write_xsams(fo, xsams_sources, sources=all_sources)

    # Environments, Functions
    write_xsams(fo, xsams_environments)
    write_xsams(fo, xsams_functions)

    # Species (ie Isotopologues) and their States
    rows = get_states_rows(q_subwhere)
    write_xsams(fo, xsams_species_with_states, rows=rows)

    write_xsams(fo, xsams_close)
    fo.close()

    end_time = time.time()
    summary_html = ['<p>Here are the results of the query in "atmos_min"'
                    ' format</p>',]
    if settings.LIMIT is not None:
        summary_html.append('<p>The number of returned transitions has '
           'been limited to a maximum of %d</p>' % settings.LIMIT)

    search_summary = {'summary_html': ''.join(summary_html)}
    search_summary['ntrans'] = 0
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]
    return output_files, search_summary

def write_xsams(fo, generator, **kwds):
    for chunk in generator(**kwds):
        print >>fo, unicode(chunk).encode('utf-8')
