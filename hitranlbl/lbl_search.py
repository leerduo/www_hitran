# -*- coding: utf-8 -*-
from django.conf import settings
import os
import re
import time
import datetime
from hitranmeta.models import Molecule, Iso, Source, RefsMap
from hitranlbl.models import State

# map globally-unique isotopologue IDs to HITRAN molecID and isoID
hitranIDs = [None,]    # no iso_id=0
isos = Iso.objects.all()
for iso in isos:
    hitranIDs.append((iso.molecule.id, iso.isoID))

def do_search(form, output_collections):
    """
    Do the search, using the search parameters parsed in the form instance
    of the LblSearchForm class.

    """
    from django import db
    from django.db import connection
    db.reset_queries()

    output_collection = output_collections[form.output_collection_index]

    return search_routines[output_collection.name](form)

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

def do_search_comprehensive(form):
    start_time = time.time()
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(pk__in=form.selected_isoIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)

    q_conds = ['t.%s' % q_cond for q_cond in get_basic_conditions(
                                            iso_ids_list, form)]

    q_fields = ['t.iso_id', 't.nu', 't.Elower', 't.gp', 't.gpp', 
                'statep_id', 'statepp_id',
                'GROUP_CONCAT(p.name, "=", p.val)',
                'GROUP_CONCAT(p.name, "=", p.err)',
                'GROUP_CONCAT(p.name, "=", p.source_id)']
    q_from = 'hitranlbl_trans t INNER JOIN hitranlbl_prm p ON p.trans_id=t.id'
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s GROUP BY t.id'\
                 % (','.join(q_fields), q_from, q_where)
    
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

    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    output_file_list = [outpath,]

    fo = open(outpath, 'w')
    s_fmt = form.field_separator.join(
            ['%2d','%2d', '%4d', '%12.6f','%10s', '%5s', '%5s',
             '%12d', '%12d', '%s', '%s', '%s'])

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_g = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_g = form.default_entry * 5

    source_ids = set()
    state_ids = set()
    for row in rows:
        global_iso_id = row[0]
        molecule_id, local_iso_id = hitranIDs[global_iso_id]
        try:
            s_Epp = '%10.4f' % row[2]
        except TypeError:
            s_Epp = default_Epp
        try:
            s_gp = '%5d' % row[3]
        except TypeError:
            s_gp = default_g
        try:
            s_gpp = '%5d' % row[4]
        except TypeError:
            s_gpp = default_g

        statep_id = row[5]
        statepp_id = row[6]
        state_ids.add(statep_id)
        state_ids.add(statepp_id)

        # parameter values
        prm_vals = row[7]
        if prm_vals is None:
            prm_vals = ''
        prm_errs = row[8]
        if prm_errs is None:
            prm_errs = ''

        try:
            prm_refs = row[9]
            for prm_ref in prm_refs.split(','):
                prm_name, prm_ref_val = prm_ref.split('=')
                source_id = int(prm_ref_val)
                source_ids.add(source_id)
        except AttributeError:
            prm_refs = ''   # nothing in row[8]
        
        print >>fo, s_fmt % (
                    molecule_id,
                    local_iso_id,
                    global_iso_id,
                    row[1], # nu
                    s_Epp,
                    s_gp, s_gpp,
                    statep_id, statepp_id,
                    prm_vals, prm_errs, prm_refs
                    )
    fo.close()

    output_file_list.extend(write_states(form, filestem, state_ids))
    output_file_list.extend(write_sources(form, filestem, source_ids))

    return output_file_list

def do_search_atmos_min_old(form):
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
                'GROUP_CONCAT(p.name, "=", p.val)',
                'GROUP_CONCAT(p.name, "=", p.err)',
                'GROUP_CONCAT(p.name, "=", p.source_id)']
    q_from = 'hitranlbl_trans t INNER JOIN hitranlbl_prm p ON p.trans_id=t.id'
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s GROUP BY t.id'\
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

def write_atmos_min_old(filestem, rows, form):
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
            s_gpp = '%5d' % row[5]
        except TypeError:
            s_gpp = default_g

        # parameter values
        gamma_air = n_air = gamma_self = delta_air = 0. # defaults
        try:
            prms = row[6].split(',')
            for prm in prms:
                prm_name, prm_val = prm.split('=')
                exec('%s=float(prm_val)' % prm_name)
        except AttributeError:
            pass    # nothing in row[6]

        # parameter errors
        s_nu_err = s_Sw_err = s_gamma_air_err = s_n_air_err = s_gamma_self_err\
               = s_delta_air_err = default_prm_err   # defaults
        try:
            prm_errs = row[7].split(',')
            for prm_err in prm_errs:
                prm_name, prm_err_val = prm_err.split('=')
                s_prm_err_val = '%8.1e' % float(prm_err_val)
                exec('s_%s_err="%s"' % (prm_name, s_prm_err_val))
        except AttributeError:
            pass    # nothing in row[7]

        # parameter sources
        s_nu_ref = s_Sw_ref = s_gamma_air_ref = s_n_air_ref = s_gamma_self_ref\
               = s_delta_air_ref = default_prm_ref   # defaults
        try:
            prm_refs = row[8].split(',')
            for prm_ref in prm_refs:
                prm_name, prm_ref_val = prm_ref.split('=')
                source_id = int(prm_ref_val)
                source_ids.add(source_id)
                s_prm_ref_val = '%5d' % source_id
                exec('s_%s_ref="%s"' % (prm_name, s_prm_ref_val))
        except AttributeError:
            pass    # nothing in row[8]
        
        print >>fo, s_fmt % (
                    molecule_id,
                    local_iso_id,
                    row[1], # nu
                    row[2], # Sw
                    s_Epp,
                    s_gp, s_gpp,
                    gamma_air, gamma_self, n_air, delta_air,
                    s_nu_err, s_Sw_err, s_gamma_air_err, s_gamma_self_err,
                    s_n_air_err, s_delta_air_err,
                    s_nu_ref, s_Sw_ref, s_gamma_air_ref, s_gamma_self_ref,
                    s_n_air_ref, s_delta_air_ref
                    )

    fo.close()

    output_file_list.extend(write_sources(form, filestem, source_ids))

    return output_file_list

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
      ' LEFT OUTER JOIN prm_gamma_air p_gamma_air ON p_gamma_air.trans_id=t.id'\
      ' LEFT OUTER JOIN prm_n_air p_n_air ON p_n_air.trans_id=t.id'\
      ' LEFT OUTER JOIN prm_gamma_self p_gamma_self ON p_gamma_self.trans_id=t.id'\
      ' LEFT OUTER JOIN prm_delta_air p_delta_air ON p_delta_air.trans_id=t.id'\
               
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

        try:
            fields[4] = '%10.4f' % row[3]
        except TypeError:
            fields[4] = default_Epp
        try:
            fields[5]= '%5d' % row[4]
        except TypeError:
            fields[5] = default_g
        try:
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

def do_search_slow(form):
    start_time = time.time()

    isos = Iso.objects.filter(pk__in=form.selected_isoIDs)

    q = Q(iso__in=isos)

    if form.numin:
        q = q & Q(nu__gte=form.numin)
    if form.numax:
        q = q & Q(nu__lte=form.numax)
    if form.Swmin:
        q = q & Q(Sw__gte=form.Swmin)
    elif form.Amin:
        q = q & Q(A__gte=form.Amin)

    q = q & Q(valid_from__lte=form.valid_on) & Q(valid_to__gte=form.valid_on)

    transitions = Trans.objects.all().filter(q).select_related()
    ntrans = transitions.count()
    end_time = time.time()
    print '%d transitions retrieved in %.1f secs' % (ntrans,
                                        end_time - start_time)

    filestem = get_filestem()
    trans_path = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)

    output_fields = output_collection.ordered()
    #oas = [os.path.splitext(x.eval_str) for x in output_fields]

    fo = open(trans_path, 'w')
    for trans in transitions:
        for i, output_field in enumerate(output_fields):
            try:
                outval = getattr(trans, output_field.name)
                print >>fo, output_field.cfmt % outval,
            except AttributeError:
                try:
                    outval = eval(output_field.eval_str)
                    print >>fo, output_field.cfmt % outval,
                except:
                    print >>fo, output_field.default,
        print >>fo
        #print >>fo, '%2d%2d%12.6f%10.3e%10.4f%5d' % (trans.iso.molecule.id, trans.iso.id, trans.nu, trans.Sw, trans.Elower, trans.gp)
    fo.close()

    end_time = time.time()

    # strip path from output filenames:
    output_files = [os.path.basename(trans_path),]
    search_summary = {'summary_html':
                '<p>Here are the results of the query in'
                ' %s format</p>' % output_collection.name}
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    print connection.queries

    return output_files, search_summary

def get_basic_conditions(iso_ids_list, form):
    q_conds = ['iso_id IN (%s)' % iso_ids_list,]
    if form.numin:
        q_conds.append('nu>=%f' % form.numin)
    if form.numax:
        q_conds.append('nu<=%f' % form.numax)
    if form.Swmin:
        q_conds.append('Sw>=%e' % form.Swmin)
    elif form.Amin:
        q_conds.append('A>=%e' % form.Amin)
    q_conds.append('valid_from <= "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    q_conds.append('valid_to > "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    return q_conds

def make_simple_sql_query(form, query_fields):
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(pk__in=form.selected_isoIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)

    q_conds = get_basic_conditions(iso_ids_list, form)

    query = 'SELECT %s FROM hitranlbl_trans WHERE %s'\
            % (','.join(query_fields), ' AND '.join(q_conds))
    print query
    return query

def get_filestem():
    if settings.TIMED_FILENAMES:
        # integer timestamp: the number of seconds since 00:00 1 January 1970
        ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    else:
        # otherwise use a fixed timestamp for generating the filename
        ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]
    return filestem

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
        #source_ids = get_source_ids(par_lines)
        #source_files = write_sources(form, filestem, source_ids)
        #output_file_list.extend(source_files)
        refIDs = get_refIDs(par_lines)
        ref_files = write_refs(form, filestem, refIDs)
        output_file_list.extend(ref_files)

    # strip path from output filenames:
    output_file_list = [os.path.basename(x) for x in output_file_list]

    return output_file_list, search_summary

def write_states(form, filestem, state_ids):
    states_path = os.path.join(settings.RESULTSPATH,
                               '%s-states.txt' % filestem)

    fo = open(states_path, 'w')
    s_fmt = form.field_separator.join(
            ['%12d', '%4d', '%10s','%5s', '%1s', '%s'])

    if form.default_entry == '-1':
        default_energy = '   -1.0000'
        default_g = '   -1'
        default_nucspin_label = '?'
    else:
        default_energy = form.default_entry * 10
        default_g = form.default_entry * 5
        default_nucspin_label = form.default_entry

    for state_id in state_ids:
        state = State.objects.filter(pk=state_id).get()
        global_iso_id = state.iso_id
        energy = state.energy
        try:
            s_energy = '%10.4f' % energy
        except TypeError:
            s_energy = default_energy
        try:
            s_g = '%5d' % state.g
        except TypeError:
            s_g = default_g
        if state.nucspin_label is None:
            s_nucspin_label = default_nucspin_label
        else:
            s_nucspin_label = '%1s' % state.nucspin_label

        print >>fo, s_fmt % (state.id, global_iso_id, s_energy, s_g,
                             s_nucspin_label, state.s_qns)
    fo.close()
    return [states_path,]

def get_refIDs(par_lines):
    molecules = Molecule.objects.all().order_by('id')
    safe_molecule_names = {}
    for molecule in molecules:
        safe_molecule_name = molecule.ordinary_formula.replace('+','p')
        safe_molecule_names[molecule.id] = safe_molecule_name
    for i, smn in enumerate(safe_molecule_names):
        print i, smn
    
    refs_set = [set(), set(), set(), set(), set(), set()]
    for par_line in par_lines:
        par_line = par_line[0]
        refs_set[0].add((par_line[:2], par_line[133:135]))  # nu
        refs_set[1].add((par_line[:2], par_line[135:137]))  # Sw / A
        refs_set[2].add((par_line[:2], par_line[137:139]))  # gamma_air
        refs_set[3].add((par_line[:2], par_line[139:141]))  # gamma_self
        refs_set[4].add((par_line[:2], par_line[141:143]))  # n_air
        refs_set[5].add((par_line[:2], par_line[143:145]))  # delta_air
    refIDs = []
    for i,prm_name in enumerate(['nu', 'S', 'gamma_air', 'gamma_self',
                                 'n_air', 'delta_air']):
        for ref_set in refs_set[i]:
            molecule_id = int(ref_set[0])
            safe_molecule_name = safe_molecule_names[molecule_id]
            refIDs.append('%s-%s-%d' % (safe_molecule_name, prm_name,
                                        int(ref_set[1])))
    return refIDs

def get_source_ids(par_lines):
    refIDs = get_refIDs(par_lines)
    refs_map = RefsMap.objects.all().filter(refID__in=refIDs)
    source_ids = [ref.source_id for ref in refs_map]
    return source_ids
        
def write_par(filestem, par_lines):
    parpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(parpath, 'w')
    # the rows from the SQL query come back as tuples with the single
    # element par_line, so we need an index here
    for par_line in par_lines:
        print >>fo, par_line[0]
    fo.close()
    return [parpath,]

def write_sources(form, filestem, source_ids):
    """
    Write sources identified by thier global source_ids within the
    relational HITRAN database.

    """

    sources_file_list = []
    if form.output_html_sources:
        sources_html_path = os.path.join(settings.RESULTSPATH,
                                '%s-sources.html' % filestem)
        write_sources_html(sources_html_path, source_ids)
        sources_file_list.append(sources_html_path)
        
    if form.output_bibtex_sources:
        sources_bib_path = os.path.join(settings.RESULTSPATH,
                                '%s-sources.bib' % filestem)
        write_sources_bibtex(sources_bib_path, source_ids)
        sources_file_list.append(sources_bib_path)
    return sources_file_list

def write_refs(form, filestem, refIDs):
    """
    Write sources identified by their native HITRAN labels,
    <molec_name>-<prm_name>-<id>.

    """

    refs_file_list = []
    if form.output_html_sources:
        refs_html_path = os.path.join(settings.RESULTSPATH,
                                '%s-refs.html' % filestem)
        write_refs_html(refs_html_path, refIDs)
        refs_file_list.append(refs_html_path)
        
    if form.output_bibtex_sources:
        refs_bib_path = os.path.join(settings.RESULTSPATH,
                                '%s-refs.bib' % filestem)
        write_refs_bibtex(refs_bib_path, refIDs)
        refs_file_list.append(refs_bib_path)
    return refs_file_list

def write_sources_html(sources_html_path, source_ids):
    fo = open(sources_html_path, 'w')
    print >>fo, '<html><head>'
    print >>fo, '<link rel="stylesheet" href="sources.css" type="text/css"'\
                ' media="screen"/>'
    print >>fo, '<link rel="stylesheet" href="sources_print.css"'\
                ' type="text/css" media="print"/>'
    print >>fo, '<meta charset="utf-8"/>'
    print >>fo, '</head><body>'

    print >>fo, '<div>'
    for source_id in sorted(source_ids):
        try:
            source = Source.objects.get(pk=source_id)
        except Source.DoesNotExist:
            print 'Warning! source not found with id', source_id
            continue
        print >>fo, '<p>%s</p>' % (
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()

def write_sources_bibtex(sources_bib_path, source_ids):
    # we need all the source_ids, even those belonging to sources cited
    # within notes, etc.
    all_source_ids = set(source_ids)
    for source in Source.objects.filter(pk__in=source_ids):
        subsources = source.source_list.all()
        for subsource in subsources:
            all_source_ids.add(subsource.id)

    fo = open(sources_bib_path, 'w')
    for source_id in sorted(list(all_source_ids)):
        try:
            source = Source.objects.get(pk=source_id)
        except Source.DoesNotExist:
            print 'Warning! source not found with id', source_id
            continue
        print >>fo, unicode(source.bibtex()).encode('utf-8')
        print >>fo
    fo.close()

def write_refs_html(refs_html_path, refIDs):
    #refs_map = RefsMap.objects.all().filter(refID__in=refIDs)
    #source_ids = [ref.source_id for ref in refs_map]

    fo = open(refs_html_path, 'w')
    print >>fo, '<html><head>'
    print >>fo, '<link rel="stylesheet" href="sources.css" type="text/css"'\
                ' media="screen"/>'
    print >>fo, '<link rel="stylesheet" href="sources_print.css"'\
                ' type="text/css" media="print"/>'
    print >>fo, '<meta charset="utf-8"/>'
    print >>fo, '</head><body>'

    print >>fo, '<div>'
    for refID in sorted(refIDs):
        try:
            source_id = RefsMap.objects.get(refID=refID).source_id
        except RefsMap.DoesNotExist:
            if refID.endswith('-0'):
                # missing sources with refID = <molec_name>-<prm_name>-0
                # default to HITRAN86 paper:
                source_id = 1
            else:
                raise
        source = Source.objects.get(pk=source_id)
        print >>fo, '<p><span style="text-decoration: underline">%s</span>'\
                    '<br/>%s</p>' % (unicode(refID).encode('utf-8'),
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()

def write_refs_bibtex(refs_bib_path, refIDs):

    def get_source_id_from_refID(refID):
        """
        Get the source id (primary key to the hitranmeta_source row) from
        the HITRAN-style refID, <molec_name>-<prm_name>-<id>.

        """
        try:
            source_id = RefsMap.objects.get(refID=refID).source_id
        except RefsMap.DoesNotExist:
            if refID.endswith('-0'):
                # missing sources with refID = <molec_name>-<prm_name>-0
                # default to HITRAN86 paper:
                source_id = 1
            else:
                raise
        return source_id

    def add_source_to_list(source_id, refID):
        """
        Add the refID to the list in the source_ids dictionary, keyed by
        source_id. Return True if this source was added for the first time,
        or False if refID was appended to the list of an existing source.

        """
        try:
            source_ids[source_id].append(refID)
            return False
        except KeyError:
            source_ids[source_id] = [refID,]
            return True
        except:
            raise

    fo = open(refs_bib_path, 'w')
    source_ids = {}

    for refID in sorted(refIDs):
        source_id = get_source_id_from_refID(refID)
        add_source_to_list(source_id, refID)
        source = Source.objects.get(pk=source_id)
        subsources = source.source_list.all()
        for i, subsource in enumerate(subsources):
            # add subsources with appended 'a', 'b', ...
            add_source_to_list(subsource.id, refID + chr(i%26+97))

    for source_id, refIDs_list in source_ids.items():
        source = Source.objects.get(pk=source_id)
        print >>fo, ', '.join(refIDs_list)
        print >>fo, unicode(source.bibtex()).encode('utf-8')
    fo.close()
    
search_routines = {
        'HITRAN2004+': do_search_par,
        'min': do_search_min,
        'atmos-min': do_search_atmos_min,
        'comprehensive': do_search_comprehensive,
}
