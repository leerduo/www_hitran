# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from models import *
from django.db.models import Q
from hitranmeta.models import Molecule, OutputCollection, Iso, Source
from lbl_searchform import LblSearchForm
import os
import time
import datetime
from itertools import chain

# get a list of molecule objects with entries in the Trans table
p_ids = Trans.objects.values('iso__molecule').distinct()
present_molecules = Molecule.objects.filter(molecID__in=p_ids)
molec_isos = {}
molec_isos[4] = Iso.objects.all().filter(molecule=present_molecules[3])

# map globally-unique isotopologue IDs to HITRAN molecID and isoID
hitranIDs = [(0,0),]    # no iso_id=0
isos = Iso.objects.all()
for iso in isos:
    hitranIDs.append((iso.molecule.molecID, iso.isoID))

output_collections = OutputCollection.objects.all()

def index(request):
    if request.POST:
        form = LblSearchForm(request.POST)
        form_valid, msg = form.is_valid()
        if form_valid:
            output_files, search_summary = do_search(form)
            c = {'search_summary': search_summary,
                 'output_files': output_files}
        else:
            c = {'search_summary': {'summary_html': '<p>There were errors in'
                ' your search parameters:</p>%s' % msg}}
        return render_to_response('lbl_searchresults.html', c)

    c = {}
    c.update(csrf(request))
    c['present_molecules'] = present_molecules
    c['molec_isos'] = molec_isos
    c['output_collections'] = output_collections
    return render_to_response('index.html', c)

def do_search(form):
    """
    Do the search, using the search parameters parsed in the form instance
    of the LblSearchForm class.

    """

    output_collection = output_collections[form.output_collection_index]

    if output_collection.name == 'HITRAN2004+':
        return do_search_par(form)
    if output_collection.name == 'astro-min':
        return do_search_astro_min(form)
    if output_collection.name == 'atmos-min':
        return do_search_atmos_min(form)
    if output_collection.name == 'test':
        return do_search_test(form)
    if output_collection.name == 'testO2':
        return do_search_testO2(form)
    print 'unknown collection!'
    return [], {}

def make_sql_query(form, fields):
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)
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

    query = 'SELECT %s FROM hitranlbl_trans WHERE %s'\
            % (','.join(fields), ' AND '.join(q_conds))
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

def do_search_atmos_min(form):
    """
    The minimal set of returned columns for atmospheric applications.

    """

    start_time = time.time()

    # just the isotopologue ids
    iso_ids = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)
    q_conds = ['t.iso_id IN (%s)' % iso_ids_list,]
    if form.numin:
        q_conds.append('nu>=%f' % form.numin)
    if form.numax:
        q_conds.append('nu<=%f' % form.numax)
    if form.Swmin:
        q_conds.append('Sw>=%e' % form.Swmin)
    elif form.Amin:
        q_conds.append('A>=%e' % form.Amin)
    q_conds.append('p.name IN ("gamma_air", "gamma_self", "n_air",'\
                             ' "delta_air")')
    q_conds.append('valid_from <= "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    q_conds.append('valid_to > "%s"' % form.valid_on.strftime('%Y-%m-%d'))

    q_fields = ['t.id', 't.iso_id', 't.nu', 't.Sw',
            't.Elower', 't.gp', 't.statep_id', 't.statepp_id',
            'GROUP_CONCAT(p.name, "=", p.val)']
    q_from = 'hitranlbl_trans t INNER JOIN hitranlbl_prm p ON p.trans_id=t.id'
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s GROUP BY t.id'\
                 % (','.join(q_fields), q_from, q_where)

    search_summary = {'summary_html':
                '<p>Here are the results of the query in '\
                ' atmos-min format</p>'}

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    ntrans = len(rows)
    te = time.time()
    print 'time to get transitions = %.1f secs' % (te - start_time)

    ts = time.time()
    filestem = get_filestem()
    output_files = write_atmos_min(filestem, form, rows)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary 

def write_atmos_min(filestem, form, rows):
    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(outpath, 'w')

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_gp = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_gp = form.default_entry * 5

    for row in rows:
        try:
            s_Epp = '%10.4f' % row[4]
        except TypeError:
            s_Epp = default_Epp
        try:
            s_gp = '%5d' % row[5]
        except TypeError:
            s_gp = default_gp
        prms = row[8].split(',')
        # NB the defaults for these parameters are 0.
        s_n_air = ' 0.0000'
        s_gamma_self = '0.0000'
        s_delta_air = ' 0.000000'
        for prm in prms:
            prm_name, prm_val = prm.split('=')
            exec('s_%s=prm_val' % prm_name)
        if len(prms) > 3:
            s_delta_air = '%s' % prms[3].split('=')[1]

        molecID, isoID = hitranIDs[row[1]]
        print >>fo, '%12d%2d%1d%12.6f%10.3e%10s%5s%12d%12d %6s %6s %7s %9s'\
            % (row[0], molecID, isoID,
               row[2], row[3], s_Epp, s_gp, row[6], row[7],
               s_gamma_air, s_gamma_self, s_n_air, s_delta_air)
    fo.close()
    return [outpath,]

def do_search_astro_min(form):
    """
    The minimal set of returned columns for astronomical applications.

    """

    start_time = time.time()

    query = make_sql_query(form, ['id', 'iso_id', 'nu', 'A', 'Elower', 'gp',
                                  'gpp', 'statep_id', 'statepp_id'])

    search_summary = {'summary_html':
                '<p>Here are the results of the query in '\
                ' astro-min format</p>'}

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    ntrans = len(rows)
    te = time.time()
    print 'time to get transitions = %.1f secs' % (te - start_time)

    ts = time.time()
    filestem = get_filestem()
    output_files = write_astro_min(filestem, form, rows)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_astro_min(filestem, form, rows):
    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(outpath, 'w')

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_gp = '   -1'
        default_gpp = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_gp = default_gpp = form.default_entry * 5

    for row in rows:
        try:
            s_Epp = '%10.4f' % row[4]
        except TypeError:
            s_Epp = default_Epp
        try:
            s_gp = '%5d' % row[5]
        except TypeError:
            s_gp = default_gp
        try:
            s_gpp = '%5d' % row[6]
        except TypeError:
            s_gpp = default_gpp
        print >>fo, '%12d%4d%12.6f%10.3e%s%s%s%12d%12d' % (row[0], row[1],
            row[2], row[3], s_Epp, s_gp, s_gpp, row[7], row[8])
    fo.close()
    return [outpath,]

def do_search_par(form):
    """
    Do the search as a raw SQL query, returning the native HITRAN2004+ 160-
    byte format.

    """

    start_time = time.time()

    query = make_sql_query(form, ['par_line',])

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
    print 'time to get transitions = %.1f secs' % (te - start_time)

    ts = time.time()
    filestem = get_filestem()
    output_files = write_par(filestem, par_lines)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def write_par(filestem, par_lines):
    parpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(parpath, 'w')
    # the rows from the SQL query come back as tuples with the single
    # element par_line, so we need an index here
    for par_line in par_lines:
        print >>fo, par_line[0]
    fo.close()
    return [parpath,]

def do_search_test(form):
    """
    A test output collection.

    """

    start_time = time.time()

    # just the isotopologue ids
    iso_ids = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)
    q_conds = ['t.iso_id IN (%s)' % iso_ids_list,]
    if form.numin:
        q_conds.append('nu>=%f' % form.numin)
    if form.numax:
        q_conds.append('nu<=%f' % form.numax)
    if form.Swmin:
        q_conds.append('Sw>=%e' % form.Swmin)
    elif form.Amin:
        q_conds.append('A>=%e' % form.Amin)
    q_conds.append('p.name IN ("nu", "Sw", "gamma_air", "gamma_self",'\
                              '"n_air", "delta_air", "gamma_H2O")')
    q_conds.append('valid_from <= "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    q_conds.append('valid_to > "%s"' % form.valid_on.strftime('%Y-%m-%d'))

    q_fields = ['t.id', 't.iso_id',
            't.Elower', 't.gp', 't.statep_id', 't.statepp_id',
            'GROUP_CONCAT(p.name, "=", p.val)',
            'GROUP_CONCAT(p.name, "=", p.err)',
            'GROUP_CONCAT(p.name, "=", p.source_id)']
    q_from = 'hitranlbl_trans t INNER JOIN hitranlbl_prm p ON p.trans_id=t.id'
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s GROUP BY t.id'\
                 % (','.join(q_fields), q_from, q_where)

    search_summary = {'summary_html':
                '<p>Here are the results of the query in '\
                ' test format</p>'}

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    ntrans = len(rows)
    te = time.time()
    print 'time to get transitions = %.1f secs' % (te - start_time)

    ts = time.time()
    filestem = get_filestem()
    output_files = write_test(filestem, form, rows)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary 

def write_test(filestem, form, rows):
    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(outpath, 'w')

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_gp = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_gp = form.default_entry * 5

    source_ids = set()
    for row in rows:
        try:
            s_Epp = '%10.4f' % row[2]
        except TypeError:
            s_Epp = default_Epp
        try:
            s_gp = '%5d' % row[3]
        except TypeError:
            s_gp = default_gp

        # parameter values
        prms = row[6].split(',')
        # NB the defaults for these parameters are 0.
        nu = -1.
        Sw = -1.
        n_air = 0.
        gamma_self = 0.
        delta_air = 0.
        gamma_H2O = 0.
        for prm in prms:
            prm_name, prm_val = prm.split('=')
            exec('%s=float(prm_val)' % prm_name)
        # parameter sources
        prm_refs = row[8].split(',')
        # XXX sort out the default character thing later...
        nu_ref = 0
        Sw_ref = 0
        gamma_air_ref = 0
        n_air_ref = 0
        gamma_self_ref = 0
        delta_air_ref = 0
        gamma_H2O_ref = 0
        for prm in prm_refs:
            prm_name, prm_ref = prm.split('=')
            i_prm_ref = int(prm_ref)
            exec('%s_ref=i_prm_ref' % prm_name)
            source_ids.add(i_prm_ref)

        molecID, isoID = hitranIDs[row[1]]
        print >>fo, '%12d %2d%1d %12.6f%4d %10.3e%4d '\
                    '%10s%5s %6.4f%4d %6.4f%4d %7.4f%4d'\
                    '%9.6f%4d %6.4f%4d'\
            % (row[0], molecID, isoID,
               nu, nu_ref,
               Sw, Sw_ref,
               s_Epp, s_gp, 
               gamma_air, gamma_air_ref,
               gamma_self, gamma_self_ref,
               n_air, n_air_ref,
               delta_air, delta_air_ref,
               gamma_H2O, gamma_H2O_ref)
    fo.close()

    sourcespath = os.path.join(settings.RESULTSPATH, '%s-sources.html'
                                                    % filestem)
    write_sources_html(sourcespath, source_ids)

    return [outpath,sourcespath]

def do_search_testO2(form):
    """
    A test output collection for O2, including Galatry parameters.

    """

    start_time = time.time()

    # just the isotopologue ids
    iso_ids = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)
    q_conds = ['t.iso_id IN (%s)' % iso_ids_list,]
    if form.numin:
        q_conds.append('nu>=%f' % form.numin)
    if form.numax:
        q_conds.append('nu<=%f' % form.numax)
    if form.Swmin:
        q_conds.append('Sw>=%e' % form.Swmin)
    elif form.Amin:
        q_conds.append('A>=%e' % form.Amin)
    q_conds.append('p.name IN ("nu", "Sw", "gamma_air", "gamma_self",'\
                             ' "n_air", "delta_air", "G_gamma_air",'\
                             ' "G_eta_air", "G_gamma_self", "G_eta_self")')
    q_conds.append('valid_from <= "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    q_conds.append('valid_to > "%s"' % form.valid_on.strftime('%Y-%m-%d'))

    q_fields = ['t.id', 't.iso_id',
            't.Elower', 't.gp', 't.statep_id', 't.statepp_id',
            'GROUP_CONCAT(p.name, "=", p.val)',
            'GROUP_CONCAT(p.name, "=", p.source_id)']
    q_from = 'hitranlbl_trans t INNER JOIN hitranlbl_prm p ON p.trans_id=t.id'
               
    q_where = ' AND '.join(q_conds)
    query = 'SELECT %s FROM %s WHERE %s GROUP BY t.id'\
                 % (','.join(q_fields), q_from, q_where)

    search_summary = {'summary_html':
                '<p>Here are the results of the query in '\
                ' testO2 format</p>'}

    # here's where we do the rawest of the raw SQL query
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    ntrans = len(rows)
    te = time.time()
    print 'time to get transitions = %.1f secs' % (te - start_time)

    ts = time.time()
    filestem = get_filestem()
    output_files = write_testO2(filestem, form, rows)
    te = time.time()
    print 'time to write transitions = %.1f secs' % (te - ts)

    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = ntrans
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary 

def write_testO2(filestem, form, rows):
    outpath = os.path.join(settings.RESULTSPATH, '%s-trans.txt' % filestem)
    fo = open(outpath, 'w')

    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_gp = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_gp = form.default_entry * 5

    source_ids = set()
    for row in rows:
        try:
            s_Epp = '%10.4f' % row[2]
        except TypeError:
            s_Epp = default_Epp
        try:
            s_gp = '%5d' % row[3]
        except TypeError:
            s_gp = default_gp

        # parameter values
        prms = row[6].split(',')
        # NB the defaults for these parameters are 0.
        nu = -1.
        Sw = -1.
        n_air = 0.
        gamma_self = 0.
        delta_air = 0.
        G_gamma_air = 0.
        G_eta_air = 0.
        G_gamma_self = 0.
        G_eta_self = 0.
        for prm in prms:
            prm_name, prm_val = prm.split('=')
            exec('%s=float(prm_val)' % prm_name)
        # parameter sources
        try:
            prm_refs = row[7].split(',')
        except AttributeError:  # Oops: prm_refs is None
            prm_refs = []
        # XXX sort out the default character thing later...
        nu_ref = 0
        Sw_ref = 0
        gamma_air_ref = 0
        n_air_ref = 0
        gamma_self_ref = 0
        delta_air_ref = 0
        G_gamma_air_ref = 0.
        G_eta_air_ref = 0.
        G_gamma_self_ref = 0.
        G_eta_self_ref = 0.
        for prm in prm_refs:
            prm_name, prm_ref = prm.split('=')
            i_prm_ref = int(prm_ref)
            exec('%s_ref=i_prm_ref' % prm_name)
            source_ids.add(i_prm_ref)

        molecID, isoID = hitranIDs[row[1]]
        print >>fo, '%12d %2d%1d %12.6f[%4d] %10.3e[%4d] '\
                    '%10s%5s %6.4f[%4d] %6.4f[%4d] %7.4f[%4d]'\
                    '%9.6f[%4d] %6.4f[%4d]'\
                    ' %6.4f[%4d] %6.4f[%4d] %6.4f[%4d]'\
            % (row[0], molecID, isoID,
               nu, nu_ref,
               Sw, Sw_ref,
               s_Epp, s_gp, 
               gamma_air, gamma_air_ref,
               gamma_self, gamma_self_ref,
               n_air, n_air_ref,
               delta_air, delta_air_ref,
               G_gamma_air, G_gamma_air_ref,
               G_eta_air, G_eta_air_ref,
               G_gamma_self, G_gamma_self_ref,
               G_eta_self, G_eta_self_ref)
    fo.close()

    sourcespath = os.path.join(settings.RESULTSPATH, '%s-sources.html'
                                                    % filestem)
    write_sources_html(sourcespath, source_ids)

    return [outpath,sourcespath]

def write_sources_html(sourcespath, source_ids):
    fo = open(sourcespath, 'w')
    print >>fo, '<html><head>'
    print >>fo, '<link rel="stylesheet" href="sources.css" type="text/css"'\
                ' media="screen"/>'
    print >>fo, '<link rel="stylesheet" href="sources_print.css"'\
                ' type="text/css" media="print"/>'
    print >>fo, '<meta charset="utf-8"/>'
    print >>fo, '</head><body>'

    print >>fo, '<div>'
    for source_id in sorted(source_ids):
        source = Source.objects.get(pk=source_id)
        print >>fo, '<p>%s</p>' % (
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()
    
