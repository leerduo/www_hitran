# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from search_utils import get_basic_conditions, get_filestem, hitranIDs,\
                         get_iso_ids_list, get_prm_defaults, set_field,\
                         write_sources
from hitranmeta.models import Iso

def do_search_atmos_min(form):
    """
    Do the search for the "atmos_min" output collection, as a raw SQL query.

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

    # get a comma-separated string comprising a list of the ids of the
    # requested isotopologue
    iso_ids_list = get_iso_ids_list(form)

    q_conds = ['t.%s' % q_cond for q_cond in get_basic_conditions(
                                            iso_ids_list, form)]

    q_fields = ['t.iso_id', 't.nu', 't.Sw', 't.Elower', 't.gp', 't.gpp', 
                'p_nu.val', 'p_Sw.val', 'p_gamma_air.val', 'p_gamma_self.val',
                'p_n_air.val', 'p_delta_air.val',
                'p_nu.err', 'p_Sw.err', 'p_gamma_air.err', 'p_gamma_self.err',
                'p_n_air.err', 'p_delta_air.err',
                'p_nu.source_id', 'p_Sw.source_id', 'p_gamma_air.source_id',
                'p_gamma_self.source_id', 'p_n_air.source_id',
                'p_delta_air.source_id',
               ]

    q_from = 'hitranlbl_trans t'\
          ' LEFT OUTER JOIN prm_nu p_nu ON p_nu.trans_id=t.id'\
          ' LEFT OUTER JOIN prm_Sw p_Sw ON p_Sw.trans_id=t.id'\
          ' LEFT OUTER JOIN prm_gamma_air p_gamma_air'\
                       ' ON p_gamma_air.trans_id=t.id'\
          ' LEFT OUTER JOIN prm_n_air p_n_air ON p_n_air.trans_id=t.id'\
          ' LEFT OUTER JOIN prm_gamma_self p_gamma_self'\
                       ' ON p_gamma_self.trans_id=t.id'\
          ' LEFT OUTER JOIN prm_delta_air p_delta_air'\
                       ' ON p_delta_air.trans_id=t.id'\
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s'\
                 % (','.join(q_fields), q_from, q_where)
    print query

    # here's where we do our rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    ntrans = len(rows)
    te = time.time()
    print 'time to get %d transitions = %.1f secs' % (ntrans, (te-start_time))

    ts = time.time()
    filestem = get_filestem()
    output_files = write_atmos_min(filestem, rows, form)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary = {'summary_html':
            '<p>Here are the results of the query in "atmos-min" format</p>'}
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_atmos_min(filestem, rows, form):
    """
    Write the output transitions file for the "atmos-min" output collection.

    Arguments:
    filestem: the base filename without path or extension: appended with
    -trans.<ext>, -sources.<ext>, etc. to form the output filename

    rows: the rows returned from the database query; for "atmos_min" they are
    iso_id, nu, Sw, Elower, gp, gpp, [prm values], [prm errors], [prm refs]

    form: the Django-parsed Form object containing the parameters for the
    search.

    Returns:
    a list of the filenames of files created in writing the output: in this
    case, the transitions file and (optionally) the sources file.

    """

    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    output_file_list = [outpath,]

    fo = open(outpath, 'w')

    # output formatting specifiers for each field of each line of the
    # transitions list output
    fmts = ['%2d', '%2d', '%12.6f', '%10.3e', '%10s', '%5s', '%5s',
            '%6.4f', '%6.4f', '%7.4f', '%9.6f',
            '%8s', '%8s', '%8s', '%8s', '%8s', '%8s',
            '%5s', '%5s', '%5s', '%5s', '%5s', '%5s']
    s_fmt = form.field_separator.join(fmts)

    # get defaults for missing parameters
    default_Epp, default_g, default_prm_err, default_prm_ref\
            = get_prm_defaults(form)

    nfields = len(fmts)
    source_ids = set()  # keep track of which unique references we've seen
    # the fields get staged for output in this list - NB to prevent
    # contamination between transitions, *every* entry in the fields list
    # must be populated for each row, even if it is with a default value
    fields = [None] * nfields
    for row in rows:
        iso_id = row[0]
        fields[0], fields[1] = hitranIDs[iso_id]    # molecule_id, local_iso_id
        fields[2], fields[3] = row[1:3]     # nu.val, Sw.val
        fields[4] = set_field('%10.4f', row[3], default_Epp) # Epp
        fields[5] = set_field('%5d', row[4], default_g) # gp
        fields[6] = set_field('%5d', row[5], default_g) # gpp

        # parameter values: start at row[8] because we've already output nu
        # (row[6]) and Sw (row[7]) directly from the transitions table
        for i,x in enumerate(row[8:12]):
            try:
                fields[i+7] = float(x)
            except TypeError:
                fields[i+7] = 0.
                pass

        # parameter errors
        for i,x in enumerate(row[12:18]):
            try:
                #s_prm_err[i] = '%8.1e' % float(x)
                fields[i+11] = '%8.1e' % float(x)
            except TypeError:
                fields[i+11] = default_prm_err
                pass

        # parameter sources
        for i,x in enumerate(row[18:24]):
            try:
                source_ids.add(x)
                fields[i+17] = '%5d' % x
            except TypeError:
                fields[i+17] = default_prm_ref
                pass
        
        print >>fo, s_fmt % tuple(fields)

    fo.close()

    output_file_list.extend(write_sources(form, filestem, source_ids))

    return output_file_list


