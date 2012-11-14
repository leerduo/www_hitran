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
from xml.sax.saxutils import escape
from hitranmeta.models import Iso, Source
from hitranlbl.models import State
from xsams_utils import make_xsams_id, make_mandatory_tag, make_optional_tag,\
                        make_referenced_text_tag, make_datatype_tag
from xsams_hitran_functions import xsams_functions
from xsams_hitran_enivronments import xsams_environments
from xsams_hitran_broadening import xsams_broadening_air,\
                                    xsams_broadening_self, xsams_shifting_air  

XSAMS_VERSION = settings.XSAMS_VERSION
NODEID = settings.NODEID

def xsams_preamble(timestamp=None):
    """
    The XML processing instruction and root element, specifying the XSAMS
    version and Schema location.
    Also outputs a comment line with the time of the query.

    """
    yield '<?xml version="1.0" encoding="UTF-8"?>\n'
    yield '<XSAMSData xmlns="http://vamdc.org/xml/xsams/%s"' % XSAMS_VERSION
    yield ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    yield ' xmlns:cml="http://www.xml-cml.org/schema"'
    yield ' xsi:schemaLocation="http://vamdc.org/xml/xsams/%s %s">\n'\
            % (XSAMS_VERSION, settings.SCHEMA_LOCATION)
    if timestamp:
        # TODO convert no. of secs to date and time
        yield '<!-- TIMESTAMP: %s -->' % timestamp

def xsams_sources(sources):
    """
    Yields the XML for the sources in the XSAMS document.

    Arguments:
    sources: a list of sources to produce the XSAMS output for.

    """

    yield '<Sources>\n'
    for source in sources:
        #if source.source_type.source_type != "note":
        for chunk in xsams_source(source):
            yield chunk
    yield '</Sources>\n'

def xsams_source(source):
    """
    Yields the XML for an individual source in the XSAMS document.

    Arguments:
    source: an instance of the hitran_meta.models Source class.

    """

    yield '<Source sourceID="%s">' % (make_xsams_id('B', source.id),)
    author_list = source.authors.split(',')
    if source.note:
        yield '<Comments>%s</Comments>' % escape(source.note)
    yield '<Authors>'
    for author in author_list:
        yield '<Author><Name>%s</Name></Author>' % author
    yield '</Authors>'
    yield make_mandatory_tag('Title', escape(source.title), '[This source does'
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
    yield '</Source>\n'

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

def xsams_molecular_chemical_species(iso):
    """
    Yield the XML for the MolecularChemicalSpecies element describing the
    isotopologue iso.

    """

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
    yield '<StableMolecularProperties>'
    yield make_datatype_tag('MolecularWeight',iso.mass, 'amu')
    yield '</StableMolecularProperties>'
    yield '</MolecularChemicalSpecies>\n'

nucspin_isomers = {'o': 'ortho', 'm': 'meta', 'p': 'para'}
def make_nuclear_spin_isomer_tag(nucspin_label, zpe_stateRef):
    # XXX for now, refer to the ZPE of the molecule rather than the actual
    # lowest energy level of this particular nuclear spin isomer...
    nucspin_isomer = nucspin_isomers.get(nucspin_label)
    if nucspin_isomer:
        return '<NuclearSpinIsomer lowestEnergyStateRef="%s">'\
               '<Name>%s</Name></NuclearSpinIsomer>'\
                    % (zpe_stateRef, nucspin_isomer)
    return ''

def make_state_qns_xml(case_prefix, qns_xml):
    """
    Make and return the XML for this state's quantum numbers. In practice,
    this means simple wrapping the pre-prepared qns_xml string in an
    appropriately decorated <Case> tag. For that we need case_prefix.

    """

    if not qns_xml:
        return ''
    return '<Case xsi:type="%s:Case" caseID="%s" xmlns:%s="http://vamdc.org/'\
           'xml/xsams/%s/cases/%s">\n%s</Case>' % (case_prefix, case_prefix,
           case_prefix, XSAMS_VERSION, case_prefix, qns_xml)

def xsams_molecular_state(id, energy, g, nucspin_label, qns_xml, zpe_stateRef,
                          case_prefix):
    """
    Yield the XML for the State with properties given as arguments.

    """

    yield '<MolecularState stateID="%s">' % (make_xsams_id('S', id),)
    yield '<MolecularStateCharacterisation>'
    if energy is not None:
        yield make_datatype_tag('StateEnergy', energy, '1/cm',
                        attrs={'energyOrigin': zpe_stateRef})
    yield make_optional_tag('TotalStatisticalWeight', g)
    nucspin_tag = make_nuclear_spin_isomer_tag(nucspin_label, zpe_stateRef)
    if nucspin_tag:
        yield nucspin_tag
    yield '</MolecularStateCharacterisation>\n'
    yield make_state_qns_xml(case_prefix, qns_xml)
    yield '</MolecularState>\n'

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
    zpe_state_id = None
    zpe_stateRef = 'S-MISSING-ZPE'
    for row in rows:
        iso_id, id, energy, g, nucspin_label, qns_xml = row
        if iso_id != this_iso_id:
            # we've moved on to a new isotopologue
            if this_iso_id != 0:
                # close the last Molecule tag unless we're on the first iso
                yield '</Molecule>'
            yield '<Molecule speciesID="%s">' % (make_xsams_id('X', iso_id),)
            # get the Iso object from the database and write its XML
            iso = Iso.objects.filter(pk=iso_id).get()
            for chunk in xsams_molecular_chemical_species(iso):
                yield chunk
            this_iso_id = iso_id
            case_prefix = iso.case.case_prefix
            # we also need its zero-point state - get its ID and write the
            # zero-point state XML
            zpe_state_id = iso.ZPE_state_id
            # the XSAMS stateRef is used to refer to the zero-point state:
            zpe_stateRef = make_xsams_id('S', zpe_state_id)
            yield '<!-- This is the zero-point energy state for %s -->'\
                            % iso.iso_name
            zpe_state_data = State.objects.filter(pk=zpe_state_id).values_list(
                          'id', 'energy', 'g', 'nucspin_label', 'qns_xml')[0]
            for chunk in xsams_molecular_state(*zpe_state_data,
                           zpe_stateRef=zpe_stateRef, case_prefix=case_prefix):
                yield chunk
        # business as usual: write the state's XML...
        if id == zpe_state_id:
            # unless it's the zero-point state, which has already been written
            continue
        for chunk in xsams_molecular_state(id, energy, g, nucspin_label,
                                           qns_xml, zpe_stateRef, case_prefix):
            yield chunk

    yield '</Molecule>'
    yield '</Molecules>'
    yield '</Species>'

def xsams_transitions(rows):
    """
    Yield the XML for the Transitions returned by the query.

    Attributes:
    rows: a tuple of the rows returned by the database query on the
    hitranlbl_states table. Each row is itself a tuple with the contents:
    (global_)iso_id, (transition)id, statep_id, statepp_id, multipole, [nu],
    [Sw], [A], [gamma_air], [gamma_self], [n_air], [delta_air], where the
    parameter [X] is expressed in three columns: val, err, source_id.

    sources: a list of the Source objects referred to in this XSAMS file

    """

    yield '<Processes>\n'
    yield '<Radiative>\n'

    for row in rows:
        iso_id, id, statep_id, statepp_id, multipole,\
        nu_val, nu_err, nu_source_id,\
        Sw_val, Sw_err, Sw_source_id,\
        A_val, A_err, A_source_id,\
        gamma_air_val, gamma_air_err, gamma_air_source_id,\
        gamma_self_val, gamma_self_err, gamma_self_source_id,\
        n_air_val, n_air_err, n_air_source_id,\
        delta_air_val, delta_air_err, delta_air_source_id = row
        yield '<RadiativeTransition id="%s">\n' % (make_xsams_id('P', id),)
        yield '<EnergyWavelength>'
        yield make_datatype_tag('Wavenumber', nu_val, '1/cm', error=nu_err,
                src_list = [nu_source_id,])
        yield '</EnergyWavelength>\n'
        yield make_mandatory_tag('UpperStateRef', '%s' % (
                                        make_xsams_id('S', statep_id),))
        yield make_mandatory_tag('LowerStateRef', '%s' % (
                                        make_xsams_id('S', statepp_id),))
        yield '<Probability>'
        yield make_datatype_tag('TransitionProbabilityA', A_val, '1/cm',
                        error=A_err, src_list = [A_source_id,])
        yield '</Probability>\n'

        # air-broadening
        for chunk in xsams_broadening_air(gamma_air_val, gamma_air_err,
                      gamma_air_source_id, n_air_val, n_air_err,
                      n_air_source_id):
            yield chunk
        # self-broadening
        for chunk in xsams_broadening_self(gamma_self_val, gamma_self_err,
                      gamma_self_source_id):
            yield chunk
        # air-induced pressure shift
        for chunk in xsams_shifting_air(delta_air_val, delta_air_err,
                      delta_air_source_id):
            yield chunk
        yield '</RadiativeTransition>\n'

    yield '</Radiative>\n'
    yield '</Processes>\n'

def xsams_close():
    yield '</XSAMSData>'
