# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from models import *
from django.db.models import Q
from hitranmeta.models import Molecule, OutputCollection, Iso, Ref
from lbl_searchform import LblSearchForm
import os
import time
import datetime
from itertools import chain

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
        numax = transitions[TRANSLIM].nu
        transitions = Trans.objects.filter(query, Q(nu__lte=numax))
        percent_returned = float(settings.TRANSLIM)/ntrans * 100.
        print 'Results truncated to %.1f %%' % percent_returned
        ntrans = settings.TRANSLIM
    else:
        print 'Results not truncated'

    if settings.TIMED_FILENAMES:
        # integer timestamp: the number of seconds since 00:00 1 January 1970
        ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    else:
        # otherwise use a fixed timestamp for generating the filename
        ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]

    # attach the parameters to the transitions, returning their set of
    # reference IDs
    ts = time.time()
    ref_ids = attach_prms(transitions)
    te = time.time()
    print 'time to attach parameters = %.1f secs' % (te-ts)

    # get the sources (reference) from the ref_ids set
    ts = time.time()
    sources = get_sources(ref_ids)
    te = time.time()
    print 'time to get sources = %.1f secs' % (te-ts)

    # get the species and states involved in the selected transitions
    ts = time.time()
    species, nspecies, nstates = get_species(transitions)
    te = time.time()
    print 'time to get species = %.1f secs' % (te-ts)

    # here's where we make the HTML to be returned
    output_files = make_html_files(form, filestem, transitions, sources,
                                   species)
    # strip path from output filenames:
    output_files = [os.path.basename(x) for x in output_files]

    end_time = time.time()
        
    search_summary['ntrans'] = len(transitions)
    search_summary['percent_returned'] = '%.1f' % percent_returned
    search_summary['timed_at'] = '%.1f secs' % (end_time - start_time)

    return output_files, search_summary

def attach_prms(transitions):
    """
    Attach the parameters for each transition to its Trans object as
    prm.val, prm.err, and prm.ref

    """
    ref_ids = set()
    for trans in transitions:
        for prm in trans.prm_set.all():
            exec('trans.%s = prm' % prm.name)
            ref_ids.add(prm.ref_id)
    return ref_ids

def get_sources(ref_ids):
    refs = []
    for ref_id in ref_ids:
        try:
            ref = Ref.objects.get(pk=ref_id)
        except Ref.DoesNotExist:
            continue
        refs.append(ref)
    return refs

def get_species(transitions):
    """
    Return a list of the species with transitions matching the search
    parameters and attach the relevant states to them.

    """

    nstates = 0
    species = Iso.objects.filter(pk__in=transitions.values_list('iso')
                                 .distinct())
    nspecies = species.count()
    for iso in species:
        if iso.molecule.molecID == 36:
            # XXX for now, hard-code the molecular charge for NO+
            iso.molecule.charge = 1
        # all the transitions for this species:
        sptransitions = transitions.filter(iso=iso)
        # sids is all the stateIDs involved in these transitions:
        stateps = sptransitions.values_list('statep', flat=True)
        statepps = sptransitions.values_list('statepp', flat=True)
        sids = set(chain(stateps, statepps))
        # attach the corresponding states to the species:
        iso.States = State.objects.filter(pk__in = sids)
        nstates += len(sids)
    return species, nspecies, nstates

def make_html_files(form, filestem, transitions, sources, species):
    output_files = []
    output_collection = output_collections[form.output_collectionID]
    output_fields = output_collection.output_field.all()
    get_states = True
    get_refs = True

    ts = time.time()
    transpath = os.path.join(settings.RESULTSPATH, '%s-trans.html' % filestem)
    fo = open(transpath, 'w')
    print >>fo, html_preamble()
    print >>fo, '<table>'
    print >>fo, '<tr>'
    for output_field in output_fields:
        print >>fo, '<th>%s</th>' % output_field.name_html
    print >>fo, '</tr>'

    r_on, r_off = 're', 'ro'
    # pre-resolving the eval_strs massively improves performance
    eval_strs = [output_field.eval_str for eval_str in output_fields]
    for trans in transitions:
        print >>fo, '<tr class="%s">' % r_on
        for eval_str in eval_strs:
            try:
                s_val = eval(eval_str)
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
    te = time.time()
    print 'time to write transitions html = %.1f secs' % (te-ts)

    if get_states:
        ts = time.time()
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
        for iso in species:
            molecID = iso.molecule.molecID
            isoID = iso.isoID
            for state in iso.States:
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
                            molecID, isoID, s_E, s_g, s_qns)
                print >>fo, '</tr>'
                r_on, r_off = r_off, r_on
            
        print >>fo, '</table>\n</body>\n</html>'
        fo.close()
        output_files.append(statespath)
        te = time.time()
        print 'time to write states html = %.1f secs' % (te-ts)

    if get_refs:
        ts = time.time()
        refspath = os.path.join(settings.RESULTSPATH,
                      '%s-refs.html' % filestem)
        fo = open(refspath, 'w')
        print >>fo, html_refs_preamble()
        print >>fo, '<table>'
        print >>fo, '<tr><th>id</th><th>reference</th></tr>'
        r_on, r_off = 're', 'ro'
        for source in sources:
            if source is None:
                continue
            print >>fo, '<tr class="%s">' % r_on
            print >>fo, '<td class="ref">%s</td>' % source.refID
            print >>fo, '<td>',
            print >>fo, unicode(source.cited_as_html).encode('utf-8'),
            if source.url:
                print >>fo, '[<a href="%s">url</a>]' % source.url
            print >>fo, '</td>'
            print >>fo, '</tr>'
            r_on, r_off = r_off, r_on
        print >>fo, '</table>'
        fo.close()
        output_files.append(refspath)
        te = time.time()
        print 'time to write sources html = %.1f secs' % (te-ts)

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
