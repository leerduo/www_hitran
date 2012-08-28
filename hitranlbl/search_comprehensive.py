# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from search_utils import get_basic_conditions, get_filestem, hitranIDs,\
                         write_sources, write_states
from hitranmeta.models import Iso, OutputField

all_prms = ['nu', 'Sw', 'A', 'gamma_air', 'gamma_self', 'n_air',
            'delta_air']

def do_search_comprehensive(form):
    start_time = time.time()
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(pk__in=form.selected_isoIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)

    q_conds = ['t.%s' % q_cond for q_cond in get_basic_conditions(
                                            iso_ids_list, form)]

    q_fields = ['t.iso_id', 't.Elower', 't.gp', 't.gpp', 
                'statep_id', 'statepp_id']
    for prm in all_prms:
        q_fields.extend(['p_%s.val' % prm, 'p_%s.ierr' % prm,
                         'p_%s.source_id' % prm])

    q_from_list = ['hitranlbl_trans t',]
    for prm in all_prms:
        q_from_list.append('prm_%s p_%s ON p_%s.trans_id=t.id' % (prm,prm,prm))
    q_from = ' LEFT OUTER JOIN '.join(q_from_list)
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s'\
                 % (', '.join(q_fields), q_from, q_where)
    
    if settings.LIMIT is not None:
        query = '%s LIMIT %d' % (query, settings.LIMIT)

    summary_text = '<p>Here are the results of the query in "comprehensive"'\
                   ' format</p>'
    if settings.LIMIT is not None:
        summary_text = '%s\n<p>The number of returned transitions has been'\
                       ' limited to a maximum of %d'\
                            % (summary_text, settings.LIMIT)
    search_summary = {'summary_html': summary_text}
          

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
    output_files = write_comprehensive(filestem, rows, form)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_comprehensive(filestem, rows, form):
    """
    Write the output transitions file for the "comprehensive" output
    collection.
    The rows returned from the database query are:
    iso_id, nu, Elower, gp, gpp, statep_id, statepp_id, [prm values],
    [prm errors], [prm refs]

    """

    # XXX
    output_states = True

    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    output_file_list = [outpath,]

    fo = open(outpath, 'w')
    fmts = ['%2d', '%2d', '%4d', '%10s', '%5s', '%5s', '%12d', '%12d']
    for prm in all_prms:
        output_field = OutputField.objects.filter(name='%s.val' % prm).get()
        fmts.append(''.join([output_field.cfmt, '(%1d)', '[%5d]']))
    s_fmt = form.field_separator.join(fmts)

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_g = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_g = form.default_entry * 5

    nfields = 8 + 3*len(all_prms)
    source_ids = set()
    state_ids = set()
    for row in rows:
        fields = [None] * nfields
        global_iso_id = row[0]
        fields[0] = global_iso_id
        molecule_id, local_iso_id = hitranIDs[global_iso_id]
        fields[1], fields[2] = molecule_id, local_iso_id
        try:    # Epp
            fields[3] = '%10.4f' % row[1]
        except TypeError:
            fields[3] = default_Epp
        try:    # gp
            fields[4]= '%5d' % row[2]
        except TypeError:
            fields[4]= default_g
        try:    # gpp
            fields[5] = '%5d' % row[3]
        except TypeError:
            fields[5] = default_g

        statep_id = row[4]
        statepp_id = row[5]
        if output_states:
            state_ids.add(statep_id)
            state_ids.add(statepp_id)
        fields[6], fields[7] = statep_id, statepp_id

        i = 6
        while i < len(row):
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
            
        #fields[8:] = row[7:]
        #for source_id in fields[10::3]:
        #    source_ids.add(source_id)
        
        print >>fo, s_fmt % tuple(fields)

    fo.close()

    output_file_list.extend(write_states(form, filestem, state_ids))
    output_file_list.extend(write_sources(form, filestem, source_ids))

    return output_file_list
