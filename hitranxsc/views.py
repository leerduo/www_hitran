# -*- coding: utf-8 -*-
from django.http import Http404
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.db.models import Q
from hitranmeta.models import Molecule
from hitranxsc.models import Xsc
from xsc_searchform import XscSearchForm
import settings
import os
import time
import datetime
import tarfile

# get a list of molecule objects with entries in the hitranxsc_xsc table
ir_ids = Xsc.objects.filter(numin__lte=20000.).values('molecule').distinct()
uv_ids = Xsc.objects.filter(numin__gte=20000.).values('molecule').distinct()
ir_xsc_molecules = Molecule.objects.filter(pk__in=ir_ids)
uv_xsc_molecules = Molecule.objects.filter(pk__in=uv_ids)

def index(request, iruv):
    if request.POST:
        form = XscSearchForm(request.POST)
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
        return render_to_response('xsc_searchresults.html', c)

    c = {}
    c.update(csrf(request))
    if iruv == 'ir':
        c['xsc_molecules'] = ir_xsc_molecules
    elif iruv == 'uv':
        c['xsc_molecules'] = uv_xsc_molecules
    else:
        raise Http404
    return render_to_response('xsc-index.html', c)

def do_search(form):
    """
    Do the search, using the search parameters parsed in the form instance
    of the XscSearchForm class.

    """

    search_summary = {'summary_html': '<p>Success!</p>'}

    # query for the requested molecules
    query = Q(molecule__in=form.molecules)
    # query for numin, numax, Tmin, Tmax, pmin and pmax
    if form.numin:
        query = query & Q(numax__gte=form.numin)
    if form.numax:
        query = query & Q(numin__lte=form.numax)
    if form.Tmin:
        query = query & Q(T__gte=form.Tmin)
    if form.Tmax:
        query = query & Q(T__lte=form.Tmax)
    if form.pmin:
        query = query & Q(p__gte=form.pmin)
    if form.pmax:
        query = query & Q(p__lte=form.pmax)
    # query for min_sigmax: only return cross sections where sigmax is
    # greater than or equal to min_sigmax
    if form.min_sigmax:
        query = query & Q(sigmax__gte=form.min_sigmax)
    # query for the date range
    query = query & Q(valid_from__lte=form.datestamp)
    query = query & Q(valid_to__gte=form.datestamp)
    xscs = Xsc.objects.filter(query)

    # integer timestamp: the number of seconds since 00:00 1 January 1970
    ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    # XXX temporary: use a fixed, constant filestem:
    #ts_int=1285072599
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]
    output_files = []
    if 'xsc' in form.output_formats:
        output_files.extend(xscs.values('filename', 'desc'))
    if 'xsams' in form.output_formats:
        xsams_name = '%s.xsams' % filestem
        # put the XSAMS file at the top of the list of output files
        output_files.insert(0, {'filename': xsams_name, 'desc': 'XSAMS file'})

        # get the molecules involved
        molecules_query = Q(pk__in=xscs.values_list('molecule'))
        molecules = Molecule.objects.filter(molecules_query).distinct()

        # get the sources
        sourceIDs = xscs.values_list('ref', flat=True).distinct()
        sources = Ref.objects.filter(pk__in=sourceIDs)

        # write the XSAMS file
        xsams_path = os.path.join(settings.RESULTSPATH, xsams_name)
        fo = open(xsams_path, 'w')
        for xsams_chunk in make_xsams(xscs, molecules, sources, output_files):
            print >>fo, xsams_chunk.encode('utf-8')
        fo.close()

    # zip up all the files in a tgz compressed archive
    tgz_name = '%s.tgz' % filestem
    tgz_path = os.path.join(settings.RESULTSPATH, tgz_name)
    tar = tarfile.open(tgz_path, 'w:gz')
    for output_file in output_files:
        filepath = output_file['filename']
        if not filepath.endswith('.xsams'):
            filepath = os.path.join('xsc',filepath)
        tar.add(name=os.path.join(settings.RESULTSPATH, filepath),
                arcname=os.path.basename(filepath))
    tar.close()
    output_files.insert(0, {'filename': tgz_name, 'desc': 'All these'\
                            ' files in one compressed archive.'})

    return output_files, search_summary

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

bad_ref = '<Category>private communication</Category>\n<Authors>\n<Author>'\
          '<Name>C. Hill</Name></Author>\n<Author><Name>M.-L. Dubernet</Name>'\
          '</Author>\n</Authors>\n<Year>2011</Year>'

def source_xml(sources):
    if not sources:
        return
    yield '<Sources>'
    for source in sources:
        yield '<Source sourceID="BHSHD-%s">' % source.refID
        ref_type = source.ref_type
        if ref_type == 'article': ref_type = 'journal'
        if ref_type == 'note':
            # we can't do notes in XSAMS:
            yield bad_ref
            yield '</Source>'
            continue
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

def make_xsams(xscs, molecules, sources, output_files):
    yield r"""<?xml version="1.0" encoding="UTF-8"?>
<XSAMSData xmlns="http://vamdc.org/xml/xsams/0.3"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns:cml="http://www.xml-cml.org/schema"
 xsi:schemaLocation="http://vamdc.org/xml/xsams/0.3 /Users/christian/research/VAMDC/XSAMS/vamdc-working/xsams.xsd">"""

    for source in source_xml(sources):
        yield source

    yield '<Environments>'
    for xsc in xscs:
        yield '    <Environment envID="EHSHD-%d">' % xsc.id
        yield '        <Temperature><Value units="K">%.1f</Value>'\
                      '</Temperature>' % xsc.T
        if xsc.broadener:
            yield '        <TotalPressure><Value units="Torr">%.2f</Value>'\
                  '</TotalPressure>' % xsc.p
            yield '        <Composition><Species name="%s"/></Composition>'\
                    % xsc.broadener
        yield '</Environment>'
    yield '</Environments>'

    yield '<Species>'
    for molecule in molecule_xml(molecules):
        yield molecule
    yield '</Species>'

    yield '<Methods>\n    <Method methodID="MEXP">'
    yield '        <Category>experiment</Category>'
    yield '        <Description>Experimental data</Description>'
    yield '    </Method>\n</Methods>'

    yield '<Processes>'
    yield '<Radiative>'
    for i, xsc in enumerate(xscs):
        yield '<AbsorptionCrossSection envRef="EHSHD-%d"'\
              ' id="PHSHD-XSC-%d">' % (xsc.id, i)
        yield '    <Description>The absorption cross'\
              ' section for %s at %.1f K, %.1f Torr</Description>'\
                    % (xsc.molecule.ordinary_formula, xsc.T, xsc.p)
        yield '    <X parameter="nu" units="1/cm">'
        dnu = (xsc.numax - xsc.numin) / (xsc.n - 1)
        yield '        <LinearSequence count="%d" initial="%f"'\
                    ' increment="%f"/>' % (xsc.n, xsc.numin, dnu)
        yield '    </X>'
        yield '    <Y parameter="sigma" units="cm2">'
        sigma_name = xsc.filename
        sigma_name = sigma_name.replace('.xsc', '.sigma')
        output_files.append({'filename': sigma_name, 'desc': 'absorption'\
                                ' cross section list'})
        yield '    <DataFile>%s</DataFile>' % sigma_name
        yield '    </Y>'
        yield '    <Species>'
        yield '    <SpeciesRef>XHSHD-%s</SpeciesRef>' % xsc.molecule.InChIKey
        yield '    </Species>'
        yield '</AbsorptionCrossSection>' 
    yield '</Radiative>'
    yield '</Processes>'

    yield '</XSAMSData>'

