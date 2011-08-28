# -*- coding: utf-8 -*-
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from models import *
from hitranmeta.models import Molecule, OutputCollection
from lbl_searchform import LblSearchForm

# get a list of molecule objects with entries in the Trans table
p_ids = Trans.objects.values('iso__molecule').distinct()
present_molecules = Molecule.objects.filter(molecID__in=p_ids)

output_collections = OutputCollection.objects.all()

def index(request):
    if request.POST:
        form = LblSearchForm(request.POST)
        if form.is_valid():
            c = {'search_summary': {'summary_html': '<p>Success!</p>'}}
        else:
            c = {'search_summary': {'summary_html': '<p>There were errors in your'
                'search parameters!</p>'}}
        return render_to_response('lbl_searchresults.html', c)

    c = {}
    c.update(csrf(request))
    c['present_molecules'] = present_molecules
    c['output_collections'] = output_collections
    #return render_to_response('index.html', {
    #            'present_molecules': present_molecules,
    #            'output_collections': output_collections,
    #            }) 
    return  render_to_response('index.html', c)
