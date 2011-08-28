# -*- coding: utf-8 -*-
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from models import *
from django.db.models import Q
from hitranmeta.models import Molecule, OutputCollection, Iso
from lbl_searchform import LblSearchForm

# get a list of molecule objects with entries in the Trans table
p_ids = Trans.objects.values('iso__molecule').distinct()
present_molecules = Molecule.objects.filter(molecID__in=p_ids)

output_collections = OutputCollection.objects.all()

def index(request):
    if request.POST:
        form = LblSearchForm(request.POST)
        form_valid, msg = form.is_valid()
        if form_valid:
            search_summary = do_search(form)
            c = {'search_summary': search_summary}
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
    transitions = Trans.objects.filter(query)
