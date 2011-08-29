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

# Limit the number of returned transitions to TRANSLIM, if not None:
TRANSLIM = 10

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
    if TRANSLIM is not None and ntrans > TRANSLIM:
        transitions = Trans.objects.filter(query).select_related()[:TRANSLIM]
        percent_returned = float(TRANSLIM)/ntrans * 100.
        ntrans = TRANSLIM

    # integer timestamp: the number of seconds since 00:00 1 January 1970
    #ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    # XXX temporary: use a fixed, constant filestem:
    ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]
    output_files = make_html_files(form, filestem, transitions)

    end_time = time.time()
        
    search_summary['ntrans'] = len(transitions)
    search_summary['percent_returned'] = '%.1f' % percent_returned
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary
    
def make_html_files(form, filestem, transitions):
    filenames = []
    transpath = os.path.join(settings.RESULTSPATH, '%s-trans.html' % filestem)
    output_collection = output_collections[form.output_collectionID]
    output_fields = output_collection.output_field.all()
    fo = open(transpath, 'w')
    print >>fo, html_preamble()
    print >>fo, '<table>'
    print >>fo, '<tr>'
    for output_field in output_fields:
        print >>fo, '<th>%s</th>' % output_field.name_html
    print >>fo, '<th>v&rsquo;</th><th>v&rdquo;</th>'#
    print >>fo, '</tr>'
    r_on, r_off = 're', 'ro'

    field_eval = []
    prm_names = set()
    for output_field in output_fields:
        if output_field.name == 'molec_id':
            field_eval.append('"%s" %% trans.iso.molecule.molecID'
                % output_field.cfmt)
        elif output_field.name == 'iso_id':
            field_eval.append('"%s" %% trans.iso.isoID' % output_field.cfmt)
        elif output_field.name in ('Elower', 'gp', 'gpp', 'par_line',
                                   'multipole'):
            field_eval.append('"%s" %% trans.%s'
                % (output_field.cfmt, output_field.name))
        elif output_field.name == 'stateIDp':
            field_eval.append('"%s" %% trans.statep.id' % output_field.cfmt)
        elif output_field.name == 'stateIDpp':
            field_eval.append('"%s" %% trans.statepp.id' % output_field.cfmt)
        elif len(output_field.name) > 4 and output_field.name[-4:] in (
                    '.val', '.err', '.ref'):
            prm_names.add(output_field.name[:-4])
            if output_field.name[-4:] == '.ref':
                # XXX refID is actually a string: sort this out in the
                # OutputFields model...
                field_eval.append('"%%s" %% trans.%s.refID'
                    % output_field.name)
            else:
                field_eval.append('"%s" %% trans.%s' % (output_field.cfmt,
                    output_field.name))
        else:
            field_eval.append('***')

    for trans in transitions:
        # get all the parameters, and attach the ones we're going to output
        # to the Trans instance
        prms = trans.prm_set.all()
        for prm_name in prm_names:
            exec('trans.%s = prms.get(name="%s")' % (prm_name, prm_name))

        qnsp = trans.statep.qns_set #
        qnspp = trans.statepp.qns_set #
            
        print >>fo, '<tr class="%s">' % r_on
        for i, output_field in enumerate(output_fields):
            try:
                s_val = eval(field_eval[i])
            except:
                #print field_eval[i]
                s_val = '###'
            print >>fo, '<td>%s</td>' % s_val

        try:#
            s_val = qnsp.get(qn_name='v').qn_val#
        except:#
            s_val = ''#
        print >>fo, '<td>%s</td>' % s_val #
        try:#
            s_val = qnspp.get(qn_name='v').qn_val#
        except:#
            s_val = ''#
        print >>fo, '<td>%s</td>' % s_val #

        print >>fo, '</tr>'
        r_on, r_off = r_off, r_on
    print >>fo, '</table>\n</body>\n</html>'
    fo.close()
    filenames.append(transpath)

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
</style>
</head>
</body>
"""
