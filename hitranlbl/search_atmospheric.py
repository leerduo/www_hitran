# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from django.db import connection
from search_utils import get_basic_conditions, get_filestem, hitranIDs,\
                         get_iso_ids_list, get_prm_defaults, set_field,\
                         write_sources, write_states, cfmt2ffmt,\
                         get_pfn_filenames
from hitranmeta.models import Iso, OutputField

# a list of all the parameters with their own tables in the database
# TODO NB obtain this form the prm_desc table
atmospheric_prms = ['nu', 'sw', 'gamma_air', 'gamma_self', 'n_air','delta_air']

def do_search_atmospheric(form):
    """
    Do the search for the "atmospheric" output collection, by raw SQL query.

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
    # requested isotopologues
    iso_ids_list = get_iso_ids_list(form)

    # the basic constraints of the query on the transitions table
    q_conds = ['t.%s' % q_cond for q_cond in get_basic_conditions(
                                            iso_ids_list, form)]

    # the fields to return from the query
    q_fields = ['t.iso_id', 't.Elower', 't.gp', 't.gpp', 
                'statep_id', 'statepp_id']
    for prm in atmospheric_prms:
        q_fields.extend(['p_%s.val' % prm, 'p_%s.ierr' % prm,
                         'p_%s.source_id' % prm])

    # the table joins
    q_from_list = ['hitranlbl_trans t',]
    for prm in atmospheric_prms:
        q_from_list.append('prm_%s p_%s ON p_%s.trans_id=t.id' % (prm,prm,prm))
    q_from = ' LEFT OUTER JOIN '.join(q_from_list)
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s'\
                 % (', '.join(q_fields), q_from, q_where)
    print query
    
    # if we're limiting the query, here's where we add that constraint
    if settings.LIMIT is not None:
        query = '%s LIMIT %d' % (query, settings.LIMIT)

    # here's where we do the rawest of the raw SQL query
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    ntrans = len(rows)
    te = time.time()
    print 'time to get %d transitions = %.1f secs' % (ntrans, (te-start_time))

    ts = time.time()
    filestem = get_filestem()
    output_files = write_atmospheric(filestem, iso_ids_list, rows, form)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    if form.output_partition_function:
        # get the partition function filenames
        output_files.extend(get_pfn_filenames(form))

    end_time = time.time()

    summary_html = ['<p>Here are the results of the query in "atmospheric"'
                    ' format</p>',]
    if settings.LIMIT is not None:
        summary_html.append('<p>The number of returned transitions has '
           'been limited to a maximum of %d</p>' % settings.LIMIT)

    #summary_html.append('<p>C-style formatting string:<br/>'\
    #       '<span style="font-family: monospace">%s</span></p>' % s_cfmts)
    #summary_html.append('<p>Fortran-style formatting string:<br/>'\
    #       '<span style="font-family: monospace">(%s)</span></p>' % s_ffmts)
    search_summary = {'summary_html': ''.join(summary_html)}
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def get_fmts(form):
    """
    Get a list of the formatting specifiers for the output.

    """

    ocfmts = []     # output C-style format list
    iffmts = []     # input Fortran-style format list
    core_output_field_names = ['global_iso_id', 'molecule_id', 'local_iso_id',
                               'Elower', 'gp', 'gpp',
                               'statep_id', 'statepp_id']
    core_output_field_fmts = dict(OutputField.objects.filter(
                name__in=core_output_field_names).values_list('name', 'cfmt'))
    for core_output_field_name in core_output_field_names:
        ocfmts.append(core_output_field_fmts[core_output_field_name])
        iffmts.append(core_output_field_fmts[core_output_field_name])
    ocfmts[3] = '%10s'  # override Elower format
    ocfmts[4] = '%5s'   # override gp format
    ocfmts[5] = '%5s'   # override gpp format

    prm_field_names = []
    for atmospheric_prm in atmospheric_prms:
        prm_field_names.extend(['%s.val' % atmospheric_prm, 
                                '%s.ierr' % atmospheric_prm,
                                '%s.ref' % atmospheric_prm])
    prm_field_fmts = dict(OutputField.objects.filter(name__in=prm_field_names)
                        .values_list('name', 'cfmt'))
    for atmospheric_prm in atmospheric_prms:
        ocfmts.append('%s(%s)[%s]' % (
                                prm_field_fmts['%s.val' % atmospheric_prm],
                                prm_field_fmts['%s.ierr' % atmospheric_prm],
                                prm_field_fmts['%s.ref' % atmospheric_prm]))
        
        # TODO - set Fortran-style specifiers here!
        prm_ffmt = [prm_field_fmts['%s.val' % atmospheric_prm], '1X',
                    prm_field_fmts['%s.ierr' % atmospheric_prm], '2X',
                    prm_field_fmts['%s.ref' % atmospheric_prm], '1X']
        iffmts.append(''.join(prm_ffmt))
    s_cfmt = form.field_separator.join(ocfmts)
    sep_len = len(form.field_separator)
    sep_ffmt = ', '
    if sep_len > 0:
        sep_ffmt = ', %dX' % sep_len
    s_iffmts = sep_ffmt.join(iffmts)
    return s_cfmt, s_iffmts

def write_atmospheric(filestem, iso_ids_list, rows, form):
    """
    Write the output transitions file for the "atmospheric" output
    collection.
    The rows returned from the database query are:
    iso_id, Elower, gp, gpp, statep_id, statepp_id, [prm values],
    [prm errors], [prm refs]

    """

    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    output_file_list = [outpath,]

    fo = open(outpath, 'w')

    s_fmt, s_iffmts = get_fmts(form)

    # get defaults for missing parameters - NB default_prm_err and
    # default_prm_ref are ignored, because these defaults are hard-coded to 0
    default_Epp, default_g, default_prm_err, default_prm_ref\
            = get_prm_defaults(form)

    nfields = 8 + 3*len(atmospheric_prms)
    source_ids = set()
    # the fields get staged for output in this list - NB to prevent
    # contamination between transitions, *every* entry in the fields list
    # must be populated for each row, even if it is with a default value
    fields = [None] * nfields
    for row in rows:
        global_iso_id = row[0]
        fields[0] = global_iso_id
        molecule_id, local_iso_id = hitranIDs[global_iso_id]
        fields[1], fields[2] = molecule_id, local_iso_id
        fields[3] = set_field('%10.4f', row[1], default_Epp) # Epp
        fields[4] = set_field('%5d', row[2], default_g) # gp
        fields[5] = set_field('%5d', row[3], default_g) # gpp

        statep_id = row[4]
        statepp_id = row[5]
        fields[6], fields[7] = statep_id, statepp_id

        i = 6
        while i < len(row):
            # each parameter is returned with its value, integer error code
            # and source_id
            val, ierr, source_id = row[i:i+3]
            if val is None:
                fields[i+2:i+5] = 0., 0., 0   # defaults
                i += 3
                continue
            fields[i+2] = val
            fields[i+3] = ierr
            fields[i+4] = source_id
            source_ids.add(source_id)
            i += 3
            
        print >>fo, s_fmt % tuple(fields)

    fo.close()

    # write the states
    if form.output_states:
        output_file_list.extend(write_states(form, filestem, iso_ids_list))
    # write the sources
    output_file_list.extend(write_sources(form, filestem, source_ids))

    return output_file_list

