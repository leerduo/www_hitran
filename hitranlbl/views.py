# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from models import *
from django.db.models import Q
from hitranmeta.models import Molecule, OutputCollection, Iso
from lbl_searchform import LblSearchForm
import os
import time
import datetime

# get a list of molecule objects with entries in the Trans table
p_ids = Trans.objects.values('iso__molecule').distinct()
present_molecules = Molecule.objects.filter(molecID__in=p_ids)

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
    c['output_collections'] = output_collections
    return  render_to_response('index.html', c)

def do_search(form):
    """
    Do the search, using the search parameters parsed in the form instance
    of the LblSearchForm class.

    """

    start_time = time.time()

    search_summary = {'summary_html': '<p>Success!</p>'}
    isos = Iso.objects.filter(molecule__molecID__in=form.selected_molecIDs)
    # TODO detect when all isotopologues have been selected and ditch this
    # filter in that case:
    query = Q(iso__in=isos)
    if form.numin:
        query = query & Q(nu__gte=form.numin)
    if form.numax:
        query = query & Q(nu__lte=form.numax)
    if form.Swmin:
        query = query & Q(Sw__gte=form.Swmin)
    query = query & Q(valid_from__lte=form.datestamp)
    query = query & Q(valid_to__gte=form.datestamp)

    transitions = Trans.objects.filter(query).select_related().order_by('nu')
    ntrans = transitions.count()
    percent_returned = 100.
    if settings.TRANSLIM is not None and ntrans > settings.TRANSLIM:
        transitions = Trans.objects.filter(query).select_related()[:settings.TRANSLIM]
        percent_returned = float(settings.TRANSLIM)/ntrans * 100.
        ntrans = settings.TRANSLIM

    if settings.TIMED_FILENAMES:
        # integer timestamp: the number of seconds since 00:00 1 January 1970
        ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    else:
        # otherwise use a fixed timestamp for generating the filename
        ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]
    output_files = make_html_files(form, filestem, transitions)
    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = len(transitions)
    search_summary['percent_returned'] = '%.1f' % percent_returned
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def make_html_files(form, filestem, transitions):
    output_files = []
    transpath = os.path.join(settings.RESULTSPATH, '%s-trans.html' % filestem)
    output_collection = output_collections[form.output_collectionID]
    output_fields = output_collection.output_field.all()
    fo = open(transpath, 'w')
    print >>fo, html_preamble()
    print >>fo, '<table>'
    print >>fo, '<tr>'
    for output_field in output_fields:
        print >>fo, '<th>%s</th>' % output_field.name_html
    print >>fo, '</tr>'

    prm_names = set()
    get_qns = False
    for output_field in output_fields:
        if len(output_field.name) > 4 and output_field.name[-4:] in (
                    '.val', '.err', '.ref'):
            prm_names.add(output_field.name[:-4])
        elif output_field.name.startswith('q_'):
            get_qns = True

    get_states = form.get_states
    if get_states:
        states = set()

    get_refs = True
    if get_refs:
        refs = set()

    r_on, r_off = 're', 'ro'
    for trans in transitions:
        # get all the parameters, and attach the ones we're going to output
        # to the Trans instance (if there are any in the output fields)
        if prm_names:
            prms = trans.prm_set
            for prm_name in prm_names:
                exec('trans.%s = prms.get(name="%s")' % (prm_name, prm_name))
                if get_refs:
                    exec('refs.add(trans.%s.ref)' % prm_name)

        if get_states:
            states.add(trans.statep)
            states.add(trans.statepp)

        # only hit the database for the quantum numbers if we have to
        if get_qns:
            qnsp = trans.statep.qns_set
            qnspp = trans.statepp.qns_set
            
        print >>fo, '<tr class="%s">' % r_on
        for output_field in output_fields:
            try:
                s_val = eval(output_field.eval_str)
            except:
                s_val = '###'
            if output_field.name == 'par_line':
                # preserve whitespace in the par_line output:
                print >>fo, '<td><pre>%s</pre></td>' % s_val
            else:
                print >>fo, '<td>%s</td>' % s_val

        print >>fo, '</tr>'
        r_on, r_off = r_off, r_on
    print >>fo, '</table>\n</body>\n</html>'
    fo.close()
    output_files.append(transpath)

    if get_states:
        statespath = os.path.join(settings.RESULTSPATH,
                        '%s-states.html' % filestem)
        fo = open(statespath, 'w')
        print >>fo, html_preamble()
        print >>fo, '<table>'
        print >>fo, '<tr>'
        print >>fo, '<th>id</th><th>molec_id</th><th>iso_id</th>'\
                    '<th><em>E</em></th><th><em>g</em></th><th>[QNs]</th>'
        print >>fo, '</tr>'
        r_on, r_off = 're', 'ro'
        for state in states:
            try:
                s_E = '%10.4f' % state.energy
            except TypeError:
                s_E = '###'
            try:
                s_g = '%5d' % state.g
            except TypeError:
                s_g = '###'
            s_qns = state.s_qns or '###'
            print >>fo, '<tr class="%s">' % r_on
            print >>fo, '<td>%12d</td><td>%2d</td><td>%1d</td><td>%s</td>'\
                        '<td>%s</td><td>%s</td>' % (state.id,
                        state.iso.molecule.molecID, state.iso.isoID,
                        s_E, s_g, s_qns)
            r_on, r_off = r_off, r_on
            
        print >>fo, '</table>\n</body>\n</html>'
        fo.close()
        output_files.append(statespath)

    if get_refs:
        refspath = os.path.join(settings.RESULTSPATH,
                      '%s-refs.html' % filestem)
        fo = open(refspath, 'w')
        print >>fo, html_refs_preamble()
        print >>fo, '<table>'
        print >>fo, '<tr><th>id</th><th>reference</th></tr>'
        r_on, r_off = 're', 'ro'
        for ref in refs:
            if ref is None:
                continue
            print >>fo, '<tr class="%s">' % r_on
            print >>fo, '<td class="ref">%s</td>' % ref.refID
            print >>fo, '<td>',
            print >>fo, unicode(ref.cited_as_html).encode('utf-8'),
            if ref.url:
                print >>fo, '[<a href="%s">url</a>]' % ref.url
            print >>fo, '</td>'
            print >>fo, '</tr>'
            r_on, r_off = r_off, r_on
        print >>fo, '</table>'
        fo.close()
        output_files.append(refspath)

    return output_files

def html_refs_preamble():
    """
    Return the header and stylesheet preamble for the line-by-line search
    results page.

    """

    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-srict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<meta name="description" content="HITRAN line-by-line search results"/>
<title>HITRAN line-by-line search results</title>
<style type="text/css">
table {font-family: serif; text-align: left; width: 800px;}
th {background-color: #fd8;}
.re {background-color: #ddf;}
.ro {background-color: #dfd;}
.ref {font-family: Courier; text-align: right;}
</style>
</head>
</body>
"""

def html_preamble():
    """
    Return the header and stylesheet preamble for the line-by-line search
    results page.

    """

    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-srict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<meta name="description" content="HITRAN line-by-line search results"/>
<title>HITRAN line-by-line search results</title>
<style type="text/css">
table {font-family: Courier; text-align: right;}
th {background-color: #fd8;}
.re {background-color: #ddf;}
.ro {background-color: #dfd;}
pre {padding: 0 0 0 0; margin: 0 0 0 0;}
</style>
</head>
</body>
"""
