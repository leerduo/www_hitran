# -*- coding: utf-8 -*-
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.db.models import Q
from hitranmeta.models import Molecule
from hitrancia.models import CIA, CollisionPair
from cia_searchform import CIASearchForm
import settings
import os
import time
import datetime
import tarfile

collision_pairs = []
for pair in CollisionPair.objects.all():
    collision_pairs.append({'id': pair.id,
                            'pair_name_html': pair.pair_name_html()})

def index(request):
    if request.POST:
        form = CIASearchForm(request.POST)
        form_valid, msg = form.is_valid()
        if form_valid:
            output_files, search_summary = do_search(form)
            c = {'search_summary': search_summary,
                 'output_files': output_files}
        else:
            c = {'search_summary': {'summary_html':
                    '<p>There were errors in your search parameters:</p>%s'
                        % msg}
                }
        return render_to_response('cia_searchresults.html', c)

    c = {}
    c.update(csrf(request))
    c['collision_pairs'] = collision_pairs
    return render_to_response('cia-index.html', c)

def do_search(form):
    """
    Do the search, using the search parameters parsed in the form instance
    of the CIASearchForm class.

    """

    search_summary = {'summary_html': '<p>Success!</p>'}

    # query for collision pairs
    query = Q(collision_pair__in=form.collision_pairs)
    # query for numin, numax, Tmin and Tmax
    if form.numin:
        query = query & Q(numax__gte=form.numin)
    if form.numax:
        query = query & Q(numin__lte=form.numax)
    if form.Tmin:
        query = query & Q(T__gte=form.Tmin)
    if form.Tmax:
        query = query & Q(T__lte=form.Tmax)
    # query for date range
    query = query & Q(valid_from__lte=form.datestamp)
    query = query & Q(valid_to__gte=form.datestamp)
    cias = CIA.objects.filter(query)
    
    # integer timestamp: the number of seconds since 00:00 1 January 1970
    ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    # XXX temporary: use a fixed, constant filestem:
    #ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]
    output_files = []
    if 'cia' in form.output_formats:
        output_files.extend(cias.values('filename', 'desc'))
    if 'xsams' in form.output_formats:
        xsams_name = '%s.xsams' % filestem
        # put the XSAMS file at the top of the list of output files
        output_files.insert(0, {'filename': xsams_name, 'desc': 'XSAMS file'})

        # get the species (atoms or molecules) involved
        species_query = Q(pk__in=cias.values_list('molecule1'))
        species_query = species_query | Q(pk__in=cias.values_list('molecule2'))
        species = Molecule.objects.filter(species_query).distinct()

        # get the sources
        sourceIDs = cias.values_list('ref', flat=True).distinct()
        sources = Ref.objects.filter(pk__in=sourceIDs)

        # write the XSAMS file
        xsams_path = os.path.join(settings.RESULTSPATH, xsams_name)
        fo = open(xsams_path, 'w')
        for xsams_chunk in make_xsams(cias, species, sources, output_files):
            print >>fo, xsams_chunk.encode('utf-8')
        fo.close()

    # zip up all the files in a tgz compressed archive
    tgz_name = '%s.tgz' % filestem
    tgz_path = os.path.join(settings.RESULTSPATH, tgz_name)
    tar = tarfile.open(tgz_path, 'w:gz')
    for output_file in output_files:
        filepath = output_file['filename']
        if not filepath.endswith('.xsams'):
            filepath = os.path.join('cia',filepath)
        tar.add(name=os.path.join(settings.RESULTSPATH, filepath),
                arcname=os.path.basename(filepath))
    tar.close()
    output_files.insert(0, {'filename': tgz_name, 'desc': 'All these'\
                            ' files in one compressed archive.'})

    return output_files, search_summary

def atom_xml(atoms):
    if not atoms:
        return
    yield '<Atoms>'
    for atom in atoms:
        yield '    <Atom>\n    <ChemicalElement>'
        # the molecID for atoms is 1000 + nuclearcharge (1001 = H, 1018 = Ar, etc)
        yield '            <NuclearCharge>%d</NuclearCharge>' % (atom.id-1000)
        yield '            <ElementSymbol>%s</ElementSymbol>'\
                        % (atom.ordinary_formula)
        yield '        </ChemicalElement>'
        yield '        <Isotope>'
        yield '            <IsotopeParameters><MassNumber>%d</MassNumber>'\
              '</IsotopeParameters>' % atom.mass_number
        yield '            <Ion speciesID="XHSHD-%s"><IonCharge>0</IonCharge>'\
              '<InChI>%s</InChI><InChIKey>%s</InChIKey></Ion>' % (atom.InChIKey,
                        atom.InChI, atom.InChIKey)
        yield '        </Isotope>\n    </Atom>'
    yield '</Atoms>'

def molecule_xml(molecules):
    if not molecules:
        return
    yield '<Molecules>'
    for molecule in molecules:
        yield '<Molecule speciesID="XHSHD-%s">' % molecule.InChIKey
        yield '    <MolecularChemicalSpecies>'
        yield '    <OrdinaryStructuralFormula>'
        yield '        <Value>%s</Value>' % molecule.ordinary_formula
        yield '    </OrdinaryStructuralFormula>'
        yield '    <StoichiometricFormula>%s</StoichiometricFormula>'\
                        % molecule.stoichiometric_formula
        yield '    <ChemicalName><Value>%s</Value></ChemicalName>'\
                        % molecule.common_name
        yield '    <InChI>%s</InChI>' % molecule.InChI
        yield '    <InChIKey>%s</InChIKey>' % molecule.InChIKey
        yield '    </MolecularChemicalSpecies>'
        yield '</Molecule>'
    yield '</Molecules>' 

def make_optional_tag(elm_name, attr, obj):
    val = obj.__dict__[attr]
    if val is None or val == '':
        return ''
    return u'<%s>%s</%s>' % (elm_name, val, elm_name)

def source_xml(sources):
    if not sources:
        return
    yield '<Sources>'
    for source in sources:
        yield '<Source sourceID="BHSHD-%s">' % source.refID
        ref_type = source.ref_type
        if ref_type == 'article': ref_type = 'journal'
        yield '<Category>%s</Category>' % ref_type
        if source.authors:
            yield '<Authors>'
            for author in source.authors.split(','):
                yield '<Author><Name>%s</Name></Author>' % author
            yield '</Authors>'
        yield make_optional_tag('Title', 'title', source)
        yield make_optional_tag('Year', 'year', source)
        yield make_optional_tag('SourceName', 'journal', source)
        yield make_optional_tag('Volume', 'volume', source)
        yield make_optional_tag('PageBegin', 'page_start', source)
        yield make_optional_tag('PageEnd', 'page_end', source)
        yield make_optional_tag('DigitalObjectIdentifier', 'doi', source)
        yield '</Source>'
    yield '</Sources>'

def make_xsams(cias, species, sources, output_files):
    yield r"""<?xml version="1.0" encoding="UTF-8"?>
<XSAMSData xmlns="http://vamdc.org/xml/xsams/0.3"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns:cml="http://www.xml-cml.org/schema"
 xsi:schemaLocation="http://vamdc.org/xml/xsams/0.3 /Users/christian/research/VAMDC/XSAMS/vamdc-working/xsams.xsd">"""

    for source in source_xml(sources):
        yield source

    yield '<Environments>'
    for cia in cias:
        yield '    <Environment envID="EHSHD-%d"><Temperature>'\
              '<Value units="K">%.1f</Value></Temperature></Environment>'\
                    % (cia.id, cia.T)
    yield '</Environments>'

    yield '<Species>'
    atoms = []; molecules = []
    for a_species in species:
        if a_species.id > 1000 and a_species.id < 1100:
            # these 'molecules' are really atoms:
            Z = a_species.id - 1000    # nuclear charge
            # XXX for now, hard code the mass numbers for H, He and Ar:
            if Z == 1: a_species.mass_number = 1
            if Z == 2: a_species.mass_number = 4
            if Z == 18: a_species.mass_number = 40
            atoms.append(a_species)
        else:
            # these 'molecules' actually are molecules:
            molecules.append(a_species)
    for atom in atom_xml(atoms):
        yield atom
    for molecule in molecule_xml(molecules):
        yield molecule
    yield '</Species>'

    yield '<Methods>\n    <Method methodID="MEXP">'
    yield '        <Category>experiment</Category>'
    yield '        <Description>Experimental data</Description>'
    yield '    </Method>\n</Methods>'

    yield '<Processes>'
    yield '<Radiative>'
    for i, cia in enumerate(cias):
        yield '<CollisionInducedAbsorptionCrossSection envRef="EHSHD-%d"'\
              ' id="PHSHD-CIA-%d">' % (cia.id, i)
        yield '    <Description>The collision-induced absorption cross'\
              ' section for %s-%s at %.1f K</Description>'\
                    % (cia.molecule1.ordinary_formula,
                       cia.molecule2.ordinary_formula,
                       cia.T)
        yield '    <X parameter="nu" units="1/cm">'
        if cia.dnu:
            yield '        <LinearSequence count="%d" initial="%f"'\
                        ' increment="%f"/>' % (cia.n, cia.numin, cia.dnu)
        else:
            nu_name = cia.filename; nu_name = nu_name.replace('.cia', '.nu')
            output_files.append({'filename': nu_name,
                                 'desc': 'wavenumber list'})
            yield '        <DataFile>%s</DataFile>' % nu_name
        yield '    </X>'
        yield '    <Y parameter="alpha" units="cm5">'
        #yield '        <DataList n="%d" units="cm5">' % cia.n
        #yield ' 4.1 4.2 4.3 4.4'
        #yield '        </DataList>'
        alpha_name = cia.filename
        alpha_name = alpha_name.replace('.cia', '.alpha')
        output_files.append({'filename': alpha_name, 'desc': 'CIA cross'\
                                ' section list'})
        yield '    <DataFile>%s</DataFile>' % alpha_name
        if cia.has_error_file:
            err_name = cia.filename
            err_name = err_name.replace('.cia', '.err')
            output_files.append({'filename': err_name, 'desc': 'error file'})
            yield '    <ErrorFile>%s</ErrorFile>' % err_name
        elif cia.error:
            yield '    <Error>%e</Error>' % cia.error
        yield '    </Y>'
        yield '    <SpeciesRef>XHSHD-%s</SpeciesRef>'\
                        % cia.molecule1.InChIKey
        yield '    <SpeciesRef>XHSHD-%s</SpeciesRef>'\
                        % cia.molecule2.InChIKey
        yield '</CollisionInducedAbsorptionCrossSection>' 
    yield '</Radiative>'
    yield '</Processes>'

    yield '</XSAMSData>'

