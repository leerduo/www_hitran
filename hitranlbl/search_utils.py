# -*- coding: utf-8 -*-
# search_utils.py
# Christian Hill, 29/8/12
# Helper methods for writing search results from the hitranlbl Django app.

import os
import time
import datetime
from django.conf import settings
from hitranmeta.models import Molecule, Iso, Source, RefsMap
from hitranlbl.models import State

# map globally-unique isotopologue IDs to HITRAN molecID and isoID
hitranIDs = [None,]    # NB there's no iso_id=0
isos = Iso.objects.all()
for iso in isos:
    hitranIDs.append((iso.molecule.id, iso.isoID))

def get_filestem():
    """
    return the filestem for output files: the base filename without path or
    extension: this is appended with -trans.<ext>, -sources.<ext>, etc.
    to form the output filenames.

    """

    if settings.TIMED_FILENAMES:
        # integer timestamp: the number of seconds since 00:00 1 January 1970
        ts_int = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    else:
        # otherwise use a fixed timestamp for generating the filename
        ts_int=1285072598
    # make the timestamp from the hex representation of ts_int, stripping
    # off the initial '0x' characters:
    filestem = hex(ts_int)[2:]
    return filestem

def get_iso_ids_list(form):
    """
    Create a comma-separated string comprising a list of the ids of the
    isotopologues requested by the search

    Arguments:

    form: the Django-parsed Form object containing the parameters for the
    search.

    Returns:
    iso_ids_list: comma-separated string comprising a list of the ids of the
    requested isotopologues.

    """

    iso_ids = Iso.objects.filter(pk__in=form.selected_isoIDs)\
                                 .values_list('id', flat=True)
    # NB we protect against SQL injection when constructing the query
    # XXX actually, this isn't necessary since iso_ids comes from the db
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)
    return iso_ids_list

def get_basic_conditions(iso_ids_list, form):
    """
    Return a list of basic conditions for the requested search. These are
    be "AND"ed together to make the SQL query.

    Arguments:
    iso_ids_list: comma-separated string comprising a list of the ids of the
    requested isotopologues.

    form: the Django-parsed Form object containing the parameters for the
    search.

    Returns:
    q_conds: a list of constraints in SQL defining the basic conditions of
    the query.

    """

    # isotopologues
    q_conds = ['iso_id IN (%s)' % iso_ids_list,]

    # wavenumber range
    if form.numin:
        q_conds.append('nu>=%f' % form.numin)
    if form.numax:
        q_conds.append('nu<=%f' % form.numax)

    # line intensity or Einstein A-coefficient threshold:
    if form.Swmin:
        q_conds.append('Sw>=%e' % form.Swmin)
    elif form.Amin:
        q_conds.append('A>=%e' % form.Amin)

    # valid-on date:
    q_conds.append('valid_from <= "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    q_conds.append('valid_to > "%s"' % form.valid_on.strftime('%Y-%m-%d'))

    return q_conds

def make_simple_sql_query(form, query_fields):
    """
    Construct and return a simple SQL query on the hitranlbl_trans table.

    Arguments:
    form: the Django-parsed Form object containing the parameters for the
    search.

    query_fields: the names of the columns of the hitranlbl_trans to return
    in the SQL query.

    Returns:
    query: a string representing the SQL query.

    """

    # get the ids of the requested isotopologues
    iso_ids_list = get_iso_ids_list(form)

    q_conds = get_basic_conditions(iso_ids_list, form)

    query = 'SELECT %s FROM hitranlbl_trans WHERE %s'\
            % (','.join(query_fields), ' AND '.join(q_conds))
    print query
    return query

def get_prm_defaults(form):
    """
    Get default strings for the parameters Epp, g (ie gp and gpp), parameter
    errors and parameters sources, used in the output when the corresponding
    values are not present in the database.

    """
    
    # TODO pull the formats from the OutputFields table
    if form.default_entry == '-1':
        default_Epp = '   -1.0000'
        default_g = '   -1'
        default_prm_err = '    -1.0'
        default_prm_ref = '   -1'
    else:
        default_Epp = form.default_entry * 10
        default_g = form.default_entry * 5
        default_prm_err = form.default_entry * 8
        default_prm_ref = form.default_entry * 5

    return default_Epp, default_g, default_prm_err, default_prm_ref

def set_field(cfmt, val, default):
    """
    Try to set and return a field with value val to C-style format cfmt;
    return default if this fails (e.g. because val is None).

    """
    try:
        field = cfmt % val
    except TypeError:
        field = default
    return field

def write_states(form, filestem, state_ids):
    """
    Write the states with ids given in the list state_ids to the output file
    formed from filestem.

    Arguments:
    form: the Django-parsed Form object containing the parameters for the
    search.

    filestem: the base filename without path or extension: appended with
    -states.<ext>, and the relevant path to form the output states filename

    state_ids: the IDs (within the hitranlbl_state table) of the states to
    be output.

    Returns:
    a list with the single entry, states_path, which is the absolute path
    to the output states file.


    """
    states_path = os.path.join(settings.RESULTSPATH,
                               '%s-states.txt' % filestem)

    fo = open(states_path, 'w')
    fmts = ['%12d', '%4d', '%10s','%5s', '%2s', '%s']
    s_fmt = form.field_separator.join(fmts)

    # default entries for missing data
    # TODO pull the formats from the OutputFields table
    if form.default_entry == '-1':
        default_energy = '   -1.0000'
        default_g = '   -1'
        default_nucspin_label = '-1'
    else:
        default_energy = form.default_entry * 10
        default_g = form.default_entry * 5
        default_nucspin_label = ' %s' % form.default_entry

    print 'default_nucspin_label =',default_nucspin_label

    # the fields get staged for output in this list - NB to prevent
    # contamination between states, *every* entry in the fields list
    # must be populated for each row, even if it is with a default value
    fields = [None] * len(fmts)
    for state_id in state_ids:
        # XXX is this really the best way of doing this...?
        state = State.objects.filter(pk=state_id).get()
        fields[0] = state_id
        fields[1] = state.iso_id
        fields[2] = set_field('%10.4f', state.energy, default_energy)
        fields[3] = set_field('%5d', state.g, default_g)
        if state.nucspin_label is None:
            fields[4] = default_nucspin_label
        else:
            fields[4] = state.nucspin_label
        fields[5] = set_field(' %s', state.s_qns, '***')    # quantum numbers

        print >>fo, s_fmt % tuple(fields)
    fo.close()

    return [states_path,]

def get_refIDs(par_lines):
    """
    Get the unique refIDs for the parameters nu, Sw/A, gamma_air, gamma_self,
    n_air and delta_air in a list of par_lines. A refID is a string of the
    form <molec_name>-<prm_name>-<ID>, where molec_name has been cast into
    "safe" form (ie an XML-safe NSName, so no '+' characters...) and prm_name
    is one of "nu", "S" (NB not "Sw" or "A"!), "gamma_air", "gamma_self",
    "n_air", "delta_air".

    Arguments:
    par_lines: a list of rows returned by the SQL database query as tuples,
    each with the single entry, par_line.

    Returns:
    a list of the unique refIDs recovered from the par_lines

    """

    # every molecule in the database
    molecules = Molecule.objects.all().order_by('id')
    # make a dictionary mapping molecule IDs to their XML-safe, escaped names
    safe_molecule_names = {}
    for molecule in molecules:
        safe_molecule_name = molecule.ordinary_formula.replace('+','p')
        safe_molecule_names[molecule.id] = safe_molecule_name

    # a list of sets for the refIDs, where each refID is represented by a tuple
    # (molecule_id, prm_refID), with prm_refID a 2-character string, extracted
    # from the par_line. There is one such set for each of the six parameters
    refs_set = [set(), set(), set(), set(), set(), set()]
    for par_line in par_lines:
        par_line = par_line[0] # index the par_line at [0] because it's a tuple
        refs_set[0].add((par_line[:2], par_line[133:135]))  # nu
        refs_set[1].add((par_line[:2], par_line[135:137]))  # Sw / A
        refs_set[2].add((par_line[:2], par_line[137:139]))  # gamma_air
        refs_set[3].add((par_line[:2], par_line[139:141]))  # gamma_self
        refs_set[4].add((par_line[:2], par_line[141:143]))  # n_air
        refs_set[5].add((par_line[:2], par_line[143:145]))  # delta_air
    refIDs = []
    for i,prm_name in enumerate(['nu', 'S', 'gamma_air', 'gamma_self',
                                 'n_air', 'delta_air']):
        for ref_set in refs_set[i]:
            molecule_id = int(ref_set[0])
            safe_molecule_name = safe_molecule_names[molecule_id]
            # construct the refID string
            refIDs.append('%s-%s-%d' % (safe_molecule_name, prm_name,
                                        int(ref_set[1])))
    return refIDs

# XXX get_source_ids is not currently used because the method which writes
# sources for the par-style search handles this natively (because it wants
# to collect them under thier refIDs rather than throwing the refIDs list
# away.
def get_source_ids(par_lines):
    """
    Get a list of unique source_ids (primary keys to the hitranmeta_source
    table) from the par_lines returned by the SQL query on the database,
    obtained by mapping the local, HITRAN-style refIDs to source_id.

    Arguments:
    par_lines: a list of rows returned by the SQL database query as tuples,
    each with the single entry, par_line.

    Returns:
    a list of the unique source_ids identified 

    """

    refIDs = get_refIDs(par_lines)
    refs_map = RefsMap.objects.all().filter(refID__in=refIDs)
    source_ids = [ref.source_id for ref in refs_map]
    return source_ids
        
def write_sources(form, filestem, source_ids):
    """
    Write sources identified by thier global source_ids within the
    relational HITRAN database. The output formats available are HTML
    and BibTeX.

    Arguments:
    form: the Django-parsed Form object containing the parameters for the
    search.

    filestem: the base filename without path or extension: appended with
    -sources.<ext>, and the relevant path to form the output sources filename

    source_ids: the list of the source_ids (primary keys to the
    hitranmeta_source table) for the sources to be written.

    Returns: a list of absolute paths to the sources files written.

    """

    sources_file_list = []
    if form.output_html_sources:
        sources_html_path = os.path.join(settings.RESULTSPATH,
                                '%s-sources.html' % filestem)
        write_sources_html(sources_html_path, source_ids)
        sources_file_list.append(sources_html_path)
        
    if form.output_bibtex_sources:
        sources_bib_path = os.path.join(settings.RESULTSPATH,
                                '%s-sources.bib' % filestem)
        write_sources_bibtex(sources_bib_path, source_ids)
        sources_file_list.append(sources_bib_path)
    return sources_file_list

def write_sources_html(sources_html_path, source_ids):
    """
    Write the sources to an HTML output file.

    Arguments:
    sources_html_path: absolute path to the HTML file containing the
    list of sources to be written.

    source_ids: the list of the source_ids (primary keys to the
    hitranmeta_source table) for the sources to be written.

    """

    fo = open(sources_html_path, 'w')
    # TODO make this HTML standards-compliant
    print >>fo, '<html><head>'
    print >>fo, '<link rel="stylesheet" href="sources.css" type="text/css"'\
                ' media="screen"/>'
    print >>fo, '<link rel="stylesheet" href="sources_print.css"'\
                ' type="text/css" media="print"/>'
    print >>fo, '<meta charset="utf-8"/>'
    print >>fo, '</head><body>'

    print >>fo, '<div>'
    for source_id in sorted(source_ids):
        try:
            source = Source.objects.get(pk=source_id)
        except Source.DoesNotExist:
            # XXX NB because of the way the sources are collected,
            # it is normal for source_ids to contain the entry None,
            # but we need to warn if there is a genuinely missing source
            print 'Warning! source not found with id', source_id
            continue
        # output the source, along with any subsources it has, if it's a note
        print >>fo, '<p>%s</p>' % (
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()

def write_sources_bibtex(sources_bib_path, source_ids):
    """
    Write the sources to a BibTeX output file.

    Arguments:
    sources_bib_path: absolute path to the BibTeX file containing the
    list of sources to be written.

    source_ids: the list of the source_ids (primary keys to the
    hitranmeta_source table) for the sources to be written.

    """

    # we need all the source_ids, even those belonging to sources cited
    # within notes, etc.
    all_source_ids = set(source_ids)
    for source in Source.objects.filter(pk__in=source_ids):
        subsources = source.source_list.all()
        for subsource in subsources:
            all_source_ids.add(subsource.id)

    fo = open(sources_bib_path, 'w')
    for source_id in sorted(list(all_source_ids)):
        try:
            source = Source.objects.get(pk=source_id)
        except Source.DoesNotExist:
            # XXX NB because of the way the sources are collected,
            # it is normal for source_ids to contain the entry None,
            # but we need to warn if there is a genuinely missing source
            print 'Warning! source not found with id', source_id
            continue
        print >>fo, unicode(source.bibtex()).encode('utf-8')
        print >>fo
    fo.close()

def write_refs(form, filestem, refIDs):
    """
    Write sources identified by thier native HITRAN labels,
    <molec_name>-<prm_name>-<id>. The output formats available are HTML
    and BibTeX.

    Arguments:
    form: the Django-parsed Form object containing the parameters for the
    search.

    filestem: the base filename without path or extension: appended with
    -sources.<ext>, and the relevant path to form the output sources filename

    refIDs: the list of the native HITRAN-style reference lables for the
    sources to be written, in the form <molec_name>-<prm_name>-<id>.
    NB molec_name has been cast into "safe" form (ie an XML-safe NSName, so
    no '+' characters...) and prm_name is one of "nu", "S" (NB not "Sw" or
    "A"!), "gamma_air", "gamma_self", "n_air", "delta_air". 

    Returns: a list of absolute paths to the sources files written.

    """

    refs_file_list = []
    if form.output_html_sources:
        refs_html_path = os.path.join(settings.RESULTSPATH,
                                '%s-refs.html' % filestem)
        write_refs_html(refs_html_path, refIDs)
        refs_file_list.append(refs_html_path)
        
    if form.output_bibtex_sources:
        refs_bib_path = os.path.join(settings.RESULTSPATH,
                                '%s-refs.bib' % filestem)
        write_refs_bibtex(refs_bib_path, refIDs)
        refs_file_list.append(refs_bib_path)
    return refs_file_list

def write_refs_html(refs_html_path, refIDs):
    """
    Write the references to an HTML output file, collected by HITRAN-style
    refID: <molec_name>-<prm_name>-<ID>.

    Arguments:
    refs_html_path: absolute path to the HTML file containing the
    list of references to be written.

    refIDs: the list of the refIDs to be written

    """

    fo = open(refs_html_path, 'w')
    print >>fo, '<html><head>'
    print >>fo, '<link rel="stylesheet" href="sources.css" type="text/css"'\
                ' media="screen"/>'
    print >>fo, '<link rel="stylesheet" href="sources_print.css"'\
                ' type="text/css" media="print"/>'
    print >>fo, '<meta charset="utf-8"/>'
    print >>fo, '</head><body>'

    print >>fo, '<div>'
    for refID in sorted(refIDs):
        try:
            source_id = RefsMap.objects.get(refID=refID).source_id
        except RefsMap.DoesNotExist:
            if refID.endswith('-0'):
                # missing sources with refID = <molec_name>-<prm_name>-0
                # default to HITRAN86 paper:
                source_id = 1
            else:
                raise
        source = Source.objects.get(pk=source_id)
        # output the source, along with any subsources it has, if it's a note
        print >>fo, '<p><span style="text-decoration: underline">%s</span>'\
                    '<br/>%s</p>' % (unicode(refID).encode('utf-8'),
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()

def write_refs_bibtex(refs_bib_path, refIDs):
    """
    Write the references to a BibTeX output file. 

    Arguments:
    refs_bib_path: absolute path to the BibTeX file containing the
    list of references to be written.

    refIDs: the list of the refIDs to be written

    """

    def get_source_id_from_refID(refID):
        """
        Get the source id (primary key to the hitranmeta_source row) from
        the HITRAN-style refID, <molec_name>-<prm_name>-<id>.

        """
        try:
            source_id = RefsMap.objects.get(refID=refID).source_id
        except RefsMap.DoesNotExist:
            if refID.endswith('-0'):
                # missing sources with refID = <molec_name>-<prm_name>-0
                # default to HITRAN86 paper:
                source_id = 1
            else:
                raise
        return source_id

    def add_source_to_list(source_id, refID):
        """
        Add the refID to the list in the source_ids dictionary, keyed by
        source_id. Return True if this source was added for the first time,
        or False if refID was appended to the list of an existing source.

        """
        try:
            source_ids[source_id].append(refID)
            return False
        except KeyError:
            source_ids[source_id] = [refID,]
            return True
        except:
            raise

    fo = open(refs_bib_path, 'w')
    source_ids = {}

    for refID in sorted(refIDs):
        source_id = get_source_id_from_refID(refID)
        add_source_to_list(source_id, refID)
        source = Source.objects.get(pk=source_id)
        subsources = source.source_list.all()
        for i, subsource in enumerate(subsources):
            # add subsources with appended 'a', 'b', ...
            add_source_to_list(subsource.id, refID + chr(i%26+97))

    for source_id, refIDs_list in source_ids.items():
        source = Source.objects.get(pk=source_id)
        print >>fo, ', '.join(refIDs_list)
        print >>fo, unicode(source.bibtex()).encode('utf-8')
    fo.close()

