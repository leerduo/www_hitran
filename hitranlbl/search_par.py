# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from search_utils import make_simple_sql_query, get_filestem, get_refIDs,\
                         write_refs

def do_search_par(form):
    """
    Do the search as a raw SQL query, returning the native HITRAN2004+ 160-
    byte format. This type of search should be super-quick, because it doesn't
    require any table joins and outputs only one field (par_line).

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

    query = make_simple_sql_query(form, ['par_line',])

    # here's where we execute the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    par_lines = cursor.fetchall()

    ntrans = len(par_lines)
    te = time.time()
    print 'time to get %d transitions = %.1f secs' % (ntrans, (te-start_time))

    # now write the par_lines
    ts = time.time()
    filestem = get_filestem()
    output_file_list = write_par(filestem, par_lines)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    end_time = time.time()

    search_summary = {'summary_html':
                '<p>Here are the results of the query in native'\
                ' 160-byte HITRAN2004+ format</p>'}
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    if form.output_sources:
        # to output the list of sources, we first need to get their source_ids
        # from their local, native HITRAN-style by-parameter refIDs
        refIDs = get_refIDs(par_lines)
        ref_files = write_refs(form, filestem, refIDs)
        output_file_list.extend(ref_files)

    # strip path from output filenames:
    output_file_list = [os.path.basename(x) for x in output_file_list]

    return output_file_list, search_summary

def write_par(filestem, par_lines):
    """
    Write the par_lines to the output file.

    Arguments:
    filestem: the base filename without path or extension: appended with
    -trans.<ext>, -sources.<ext>, etc. to form the output filename

    par_lines: a tuple of the rows returned by the database query - each entry
    in this tuple is actually a list with one item (the par_line) in it.

    Returns:
    a list of the filenames of files created in writing the output: in this
    case, just a single filename for the output .par transitions file.

    """

    parpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(parpath, 'w')
    # the rows from the SQL query come back as tuples with the single
    # element par_line, so we need to index at [0] here
    for par_line in par_lines:
        print >>fo, par_line[0]
    fo.close()
    return [parpath,]
