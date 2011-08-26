# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from models import *
from hitranmeta.models import Molecule, OutputCollection

# get a list of molecule objects with entries in the Trans table
p_ids = Trans.objects.values('iso__molecule').distinct()
present_molecules = Molecule.objects.filter(molecID__in=p_ids)

output_collections = OutputCollection.objects.all()

def index(request):
    return render_to_response('index.html', {
                'present_molecules': present_molecules,
                'output_collections': output_collections,
                }) 
