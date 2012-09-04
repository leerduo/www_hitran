# -*- coding: utf-8 -*-
# xsams_generators.py
# Christian Hill
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# v0.1 1/9/12
# Generators for writing the various chunks of an XSAMS document.
from django.conf import settings
import urllib
from hitranmeta.models import Iso, Source
from xsams_utils import make_mandatory_tag, make_optional_tag,\
                        make_referenced_text_tag, make_datatype_tag
from xsams_hitran_functions import xsams_functions
from xsams_hitran_enivronments import xsams_environments

XSAMS_VERSION = '1.0'
NODEID = settings.NODEID

def xsams_preamble(timestamp):
    """
    The XML processing instruction and root element, specifying the XSAMS
    version and Schema location.
    Also outputs a comment line with the time of the query.

    """
    yield '<?xml version="1.0" encoding="UTF-8"?>\n'
    yield '<XSAMSData xmlns="http://vamdc.org/xml/xsams/%s"' % XSAMS_VERSION
    yield ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    yield ' xmlns:cml="http://www.xml-cml.org/schema"'
    yield ' xsi:schemaLocation="http://vamdc.org/xml/xsams/%s %s">'\
            % (XSAMS_VERSION, settings.SCHEMA_LOCATION)
    # TODO convert no. of secs to date and time
    yield '<!-- TIMESTAMP: %s -->' % timestamp

def xsams_sources(sources):
    """
    Yields the XML for the sources in the XSAMS document.

    Arguments:
    sources: a list of sources to produce the XSAMS output for.

    """

    yield '<Sources>'
    for source in sources:
        if source.source_type.source_type != "note":
            for chunk in xsams_source(source):
                yield chunk
    yield '</Sources>'

def xsams_source(source):
    """
    Yields the XML for an individual source in the XSAMS document.

    Arguments:
    source: an instance of the hitran_meta.models Source class.

    """

    yield '<Source sourceID="B%s-%d">' % (NODEID, source.id)
    author_list = source.authors.split(',')
    yield '<Authors>'
    for author in author_list:
        yield '<Author><Name>%s</Name></Author>' % author
    yield '</Authors>'
    yield make_mandatory_tag('Title', source.title, '[This source does'
                                        ' not have a title]')
    yield make_mandatory_tag('Category', source.source_type.xsams_category, '')
    # XXX what to do when the year is missing?
    yield make_mandatory_tag('Year', source.year, '2008')
    yield make_optional_tag('SourceName', source.journal)
    yield make_optional_tag('Volume', source.volume)
    yield make_optional_tag('PageBegin', source.page_start)
    yield make_optional_tag('PageEnd', source.page_end)
    yield make_optional_tag('ArticleNumber', source.article_number)
    yield make_optional_tag('UniformResourceIdentifier',
                            urllib.quote(source.url))
    yield make_optional_tag('DigitalObjectIdentifier', source.doi)
    yield '</Source>'

# TODO - replace this with something better (using the minidom?)
def get_molecule_cml_contents(cml):
    """
    Extract the contents of the <molecule> tag in the string cml, adding the
    "cml:" namespace prefix along the way. This rough-and-ready version
    assumes that each tag appears on its own line...

    """

    nscml = []
    for line in cml.split('\n'):
        line = line.strip()
        if line.startswith('<molecule'):
            continue
        if line.startswith('</molecule'):
            break
        for open_tag in ('<atom', '<bond'):
            line = line.replace(open_tag, '<cml:%s' % open_tag[1:])
        for close_tag in ('</atom', '</bond'):
            line = line.replace(close_tag, '</cml:%s' % close_tag[2:])
        nscml.append(line)
    return '\n'.join(nscml)

def xsams_molecular_chemical_species(iso_id):
    """
    Yield the XML for the MolecularChemicalSpecies element describing the
    isotopologue identified in the database by the (global) ID iso_id.

    """

    iso = Iso.objects.filter(pk=iso_id).get()
    molecule = iso.molecule
    yield '<MolecularChemicalSpecies>'
    yield make_referenced_text_tag('OrdinaryStructuralFormula', iso.iso_name,
         'An isotopologue of the molecule %s' % molecule.ordinary_formula, [])
    yield make_optional_tag('StoichiometricFormula',
                            molecule.stoichiometric_formula)
    # XXX hard-code the ion-charge for now:
    ion_charge = None
    if molecule.ordinary_formula == 'NO+':
        ion_charge = '1'
    yield make_optional_tag('IonCharge', ion_charge)
    yield make_referenced_text_tag('ChemicalName', molecule.common_name)
    yield make_optional_tag('InChI', iso.InChI)
    yield make_optional_tag('InChIKey', iso.InChIKey)
    yield make_optional_tag('MoleculeStructure',
                            get_molecule_cml_contents(iso.cml))
    yield '</MolecularChemicalSpecies>'

nucspin_isomers = {'o': 'ortho', 'm': 'meta', 'p': 'para'}
def make_nuclear_spin_isomer_tag(nucspin_label):
    nucspin_isomer = nucspin_isomers.get(nucspin_label)
    if nucspin_isomer:
        return '<NuclearSpinIsomer><Name>%s</Name></NuclearSpinIsomer>'\
                    % nucspin_isomer
    return ''

def xsams_molecular_state(id, energy, g, nucspin_label, qns_xml):
    """
    Yield the XML for the State with properties given as arguments.

    """

    yield '<MolecularState stateID="S%s-%d">' % (NODEID, id)
    yield '<MolecularStateCharacterisation>'
    yield make_datatype_tag('StateEnergy', energy)
    yield make_optional_tag('TotalStatisticalWeight', g)
    yield make_nuclear_spin_isomer_tag(nucspin_label)
    yield '</MolecularStateCharacterisation>'
    yield '</MolecularState>'

def xsams_species_with_states(rows):
    """
    Yield the XML for the Species and their States returned by the query.

    Attributes:
    rows: a tuple of the rows returned by the database query on the
    hitranlbl_states table. Each row is itself a tuple with the contents:
    (global_)iso_id, id, energy, g, nucspin_label, qns_xml

    """

    yield '<Species>'
    yield '<Molecules>'

    this_iso_id = 0
    for row in rows:
        iso_id, id, energy, g, nucspin_label, qns_xml = row
        if iso_id != this_iso_id:
            if this_iso_id != 0:
                # close the last Molecule tag unless we're on the first iso
                yield '</Molecule>'
            yield '<Molecule speciesID="X%s-%d">' % (NODEID, iso_id)
            for chunk in xsams_molecular_chemical_species(iso_id):
                yield chunk
            this_iso_id = iso_id
        for chunk in xsams_molecular_state(id, energy, g, nucspin_label,
                                           qns_xml):
            yield chunk

    yield '</Molecule>'
    yield '</Molecules>'
    yield '</Species>'
        

def xsams_close():
    yield '</XSAMSData>'
