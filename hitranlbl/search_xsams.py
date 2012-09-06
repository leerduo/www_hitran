# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from django.db import connection
import logging
log = logging.getLogger('vamdc.hitran_node')
from hitranmeta.models import Iso, Source
from search_utils import get_basic_conditions, get_filestem, get_iso_ids_list,\
                         get_all_source_ids
from xsams_queries import get_xsams_src_query, get_xsams_states_query,\
                          get_xsams_trans_query
from xsams_generators import xsams_preamble, xsams_sources, xsams_close,\
                             xsams_functions, xsams_environments,\
                             xsams_species_with_states, xsams_transitions

def get_src_ids(src_query):
    """
    Get a list of distinct source IDs for the parameters returned by the
    search.

    Arguments:
    src_query: a string of SQL comprising the query used to retrieve the
    sources

    Returns:
    src_ids: a list of distinct primary keys to the Sources referenced by
    the parameters to be returned by the query.

    """

    log.debug('Sources query: ', src_query)
    print src_query
    print 'Fetching sources...'
    st = time.time()

    cursor = connection.cursor()
    cursor.execute(src_query)
    rows = cursor.fetchall()
    src_ids = [row[0] for row in rows]  # rows is a tuple of tuples: (src_id,)
    src_ids.sort()

    et = time.time()
    print '%d sources found in %.1f secs' % (len(src_ids), et-st)
    return src_ids

def get_states_rows(st_query):
    """
    Get the states involved in the transitions selected by the query,
    ordered by their (global) isotopologue IDs.

    Arguments:
    st_query: a string of SQL comprising the query used to retrieve the
    states

    Returns:
    A tuple of the number of states retrieved, and the rows themselves

    """

    print 'Fetching states...'
    st = time.time()

    cursor = connection.cursor()
    cursor.execute(st_query)

    et = time.time()
    nstates = cursor.rowcount
    print '%d states retrieved in %.1f secs' % (nstates, (et - st))
    return nstates, cursor.fetchall()

def get_transitions_rows(t_query):
    """
    Get the transitions and associated parameters requested by the query.

    Arguments:
    t_query: a string of SQL comprising the query used to retrieve the
    transitions

    Returns:
    A tuple of the number of transitions retrieved, and the rows themselves

    """

    print 'Fetching transitions...'
    st = time.time()

    cursor = connection.cursor()
    cursor.execute(t_query)

    et = time.time()
    ntrans = cursor.rowcount
    print '%d transitions retrieved in %.1f secs' % (ntrans, (et - st))
    return ntrans, cursor.fetchall()

def get_transitions_count(tc_query):
    """
    Get and return the number of transitions that will be returned by the
    main query, using the supplied SQL query string, tc_query.

    """
    cursor = connection.cursor()
    cursor.execute(tc_query)
    ntrans = cursor.fetchone()[0]
    return ntrans

def get_isos_count(ic_query):
    """
    Get and return the number of isotopologues that will be returned by the
    main query, using the supplied SQL query string, ic_query.

    """
    cursor = connection.cursor()
    cursor.execute(ic_query)
    niso = cursor.fetchone()[0]
    return niso

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
    src_query = get_xsams_src_query(q_subwhere)
    source_ids = get_src_ids(src_query)
    # we need all the source_ids, even those belonging to sources cited
    # within notes, etc.
    all_source_ids = get_all_source_ids(source_ids)
    all_sources = Source.objects.filter(pk__in=all_source_ids)
    write_xsams(fo, xsams_sources, sources=all_sources)

    # Environments, Functions
    write_xsams(fo, xsams_environments)
    write_xsams(fo, xsams_functions)

    # Species (ie Isotopologues) and their States
    st_query = get_xsams_states_query(q_subwhere)
    nstates, rows = get_states_rows(st_query)
    write_xsams(fo, xsams_species_with_states, rows=rows)

    # Transitions
    t_query = get_xsams_trans_query(q_subwhere)
    ntrans, rows = get_transitions_rows(t_query)
    write_xsams(fo, xsams_transitions, rows=rows)

    write_xsams(fo, xsams_close)
    fo.close()

    end_time = time.time()
    summary_html = ['<p>Here are the results of the query in XSAMS'
                    ' format</p>',]
    if settings.XSAMS_LIMIT is not None:
        summary_html.append('<p>The number of returned transitions has '
           'been limited to a maximum of %d</p>' % settings.XSAMS_LIMIT)

    search_summary = {'summary_html': ''.join(summary_html)}
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]
    return output_files, search_summary

def write_xsams(fo, generator, **kwds):
    for chunk in generator(**kwds):
        print >>fo, unicode(chunk).encode('utf-8')

def xsams_generator(sql_queries, timestamp, all_sources=None, state_rows=None,
                    trans_rows=None):
    """
    The generator for an XSAMS document constructed using a set of provided
    queries.

    Arguments:
    sql_queries, a dictionary keyed by 'src_query', 'st_query', 't_query'
    for the sources query, the states query, and the transitions query
    respectively.
    timestamp: the timestamp, in iso-format, for the document (which also
    appears in the filename of the generated document).
    all_sources: a list of the Sources to be written as XSAMS, if this list
    has been pre-fetched.
    state_rows, trans_rows: the rows returned by the query for states and
    transitions respectively, if these have been pre-fetched
 
    """

    # XSAMS preamble
    for chunk in xsams_preamble(timestamp=timestamp):
        yield chunk

    # Sources
    if all_sources is None:
        source_ids = get_src_ids(sql_queries['src_query'])
        # we need all the source_ids, even those belonging to sources cited
        # within notes, etc.
        all_source_ids = get_all_source_ids(source_ids)
        all_sources = Source.objects.filter(pk__in=all_source_ids)
    for chunk in xsams_sources(sources=all_sources):
        yield chunk

    # Environments, Functions
    for chunk in xsams_environments():
        yield chunk
    for chunk in xsams_functions():
        yield chunk

    # Species (ie Isotopologues) and their States
    if state_rows is None:
        nstates, state_rows = get_states_rows(sql_queries['st_query'])
    for chunk in xsams_species_with_states(rows=state_rows):
        yield chunk

    # Transitions
    if trans_rows is None:
        ntrans, trans_rows = get_transitions_rows(sql_queries['t_query'])
    for chunk in xsams_transitions(rows=trans_rows):
        yield chunk

    # Close tag
    for chunk in xsams_close():
        yield chunk
