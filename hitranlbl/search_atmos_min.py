# -*- coding: utf-8 -*-
import os
import time
from django.conf import settings
from search_utils import get_basic_conditions, get_filestem, hitranIDs,\
                         write_sources
from hitranmeta.models import Iso

def do_search_atmos_min(form):
    start_time = time.time()
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(pk__in=form.selected_isoIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)

    q_conds = ['t.%s' % q_cond for q_cond in get_basic_conditions(
                                            iso_ids_list, form)]
    #params = ['nu', 'Sw', 'gamma_air', 'gamma_self', 'n_air', 'delta_air']
    #quoted_params = ', '.join(['"%s"' % prm_name for prm_name in params])

    #q_conds.append('p.name IN (%s)' % quoted_params)

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

    search_summary = {'summary_html':
            '<p>Here are the results of the query in "atmos-min" format</p>'}

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
    output_files = write_atmos_min(filestem, rows, form)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_atmos_min(filestem, rows, form):
    """
    Write the output transitions file for the "atmos-min" output collection.
    The rows returned from the database query are:
    iso_id, nu, Sw, Elower, gp, gpp, [prm values], [prm errors], [prm refs]

    """

    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    output_file_list = [outpath,]

    fo = open(outpath, 'w')
    s_fmt = form.field_separator.join(
            ['%2d','%2d','%12.6f','%10.3e','%10s','%5s', '%5s',
             '%6.4f', '%6.4f', '%7.4f', '%9.6f',
             '%8s', '%8s', '%8s', '%8s', '%8s', '%8s',
             '%5s', '%5s', '%5s', '%5s', '%5s', '%5s'])

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_g = '   -1'
        default_prm_err = '    -1.0'
        default_prm_ref = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_g = form.default_entry * 5
        default_prm_err = form.default_entry * 8
        default_prm_ref = form.default_entry * 5

    source_ids = set()
    for row in rows:
        fields = [None]*23
        iso_id = row[0]
        fields[0], fields[1] = hitranIDs[iso_id]
        #molecule_id, local_iso_id = hitranIDs[iso_id]

        fields[2], fields[3] = row[1:3]

        try:    # Epp
            fields[4] = '%10.4f' % row[3]
        except TypeError:
            fields[4] = default_Epp
        try:    # gp
            fields[5]= '%5d' % row[4]
        except TypeError:
            fields[5] = default_g
        try:    # gpp
            fields[6] = '%5d' % row[5]
        except TypeError:
            fields[6] = default_g

        # parameter values
        #prm = [None, None, 0., 0., 0., 0.]
        #fields[7:11] = 0.   # default parameter value
        for i,x in enumerate(row[8:12]):
            try:
                fields[i+7] = float(x)
            except TypeError:
                fields[i+7] = 0.
                pass

        # parameter errors
        #s_prm_err = [default_prm_err] * 6
        for i,x in enumerate(row[12:18]):
            try:
                #s_prm_err[i] = '%8.1e' % float(x)
                fields[i+11] = '%8.1e' % float(x)
            except TypeError:
                fields[i+11] = default_prm_err
                pass

        # parameter sources
        #s_prm_ref = [default_prm_ref] * 6
        for i,x in enumerate(row[18:24]):
            try:
                source_ids.add(x)
                #s_prm_ref[i] = '%5d' % x
                fields[i+17] = '%5d' % x
            except TypeError:
                fields[i+17] = default_prm_ref
                pass
        
        print >>fo, s_fmt % tuple(fields)

    fo.close()

    output_file_list.extend(write_sources(form, filestem, source_ids))

    return output_file_list


