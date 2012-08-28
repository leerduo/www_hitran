# -*- coding: utf-8 -*-
import os
import datetime
from django.conf import settings
from hitranmeta.models import Molecule, Iso, Source, RefsMap
from hitranlbl.models import State

# map globally-unique isotopologue IDs to HITRAN molecID and isoID
hitranIDs = [None,]    # no iso_id=0
isos = Iso.objects.all()
for iso in isos:
    hitranIDs.append((iso.molecule.id, iso.isoID))

def get_filestem():
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

def get_basic_conditions(iso_ids_list, form):
    q_conds = ['iso_id IN (%s)' % iso_ids_list,]
    if form.numin:
        q_conds.append('nu>=%f' % form.numin)
    if form.numax:
        q_conds.append('nu<=%f' % form.numax)
    if form.Swmin:
        q_conds.append('Sw>=%e' % form.Swmin)
    elif form.Amin:
        q_conds.append('A>=%e' % form.Amin)
    q_conds.append('valid_from <= "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    q_conds.append('valid_to > "%s"' % form.valid_on.strftime('%Y-%m-%d'))
    return q_conds

def make_simple_sql_query(form, query_fields):
    # just the isotopologue ids
    iso_ids = Iso.objects.filter(pk__in=form.selected_isoIDs)\
                                 .values_list('id', flat=True)

    # NB protect against SQL injection when constructing the query
    iso_ids_list = ','.join(str(int(id)) for id in iso_ids)

    q_conds = get_basic_conditions(iso_ids_list, form)

    query = 'SELECT %s FROM hitranlbl_trans WHERE %s'\
            % (','.join(query_fields), ' AND '.join(q_conds))
    print query
    return query

def write_states(form, filestem, state_ids):
    states_path = os.path.join(settings.RESULTSPATH,
                               '%s-states.txt' % filestem)

    fo = open(states_path, 'w')
    s_fmt = form.field_separator.join(
            ['%12d', '%4d', '%10s','%5s', '%1s', '%s'])

    if form.default_entry == '-1':
        default_energy = '   -1.0000'
        default_g = '   -1'
        default_nucspin_label = '?'
    else:
        default_energy = form.default_entry * 10
        default_g = form.default_entry * 5
        default_nucspin_label = form.default_entry

    for state_id in state_ids:
        state = State.objects.filter(pk=state_id).get()
        global_iso_id = state.iso_id
        energy = state.energy
        try:
            s_energy = '%10.4f' % energy
        except TypeError:
            s_energy = default_energy
        try:
            s_g = '%5d' % state.g
        except TypeError:
            s_g = default_g
        if state.nucspin_label is None:
            s_nucspin_label = default_nucspin_label
        else:
            s_nucspin_label = '%1s' % state.nucspin_label

        print >>fo, s_fmt % (state.id, global_iso_id, s_energy, s_g,
                             s_nucspin_label, state.s_qns)
    fo.close()
    return [states_path,]

def get_refIDs(par_lines):
    molecules = Molecule.objects.all().order_by('id')
    safe_molecule_names = {}
    for molecule in molecules:
        safe_molecule_name = molecule.ordinary_formula.replace('+','p')
        safe_molecule_names[molecule.id] = safe_molecule_name
    
    refs_set = [set(), set(), set(), set(), set(), set()]
    for par_line in par_lines:
        par_line = par_line[0]
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
            refIDs.append('%s-%s-%d' % (safe_molecule_name, prm_name,
                                        int(ref_set[1])))
    return refIDs

def get_source_ids(par_lines):
    refIDs = get_refIDs(par_lines)
    refs_map = RefsMap.objects.all().filter(refID__in=refIDs)
    source_ids = [ref.source_id for ref in refs_map]
    return source_ids
        
def write_sources(form, filestem, source_ids):
    """
    Write sources identified by thier global source_ids within the
    relational HITRAN database.

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

def write_refs(form, filestem, refIDs):
    """
    Write sources identified by their native HITRAN labels,
    <molec_name>-<prm_name>-<id>.

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

def write_sources_html(sources_html_path, source_ids):
    fo = open(sources_html_path, 'w')
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
            print 'Warning! source not found with id', source_id
            continue
        print >>fo, '<p>%s</p>' % (
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()

def write_sources_bibtex(sources_bib_path, source_ids):
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
            print 'Warning! source not found with id', source_id
            continue
        print >>fo, unicode(source.bibtex()).encode('utf-8')
        print >>fo
    fo.close()

def write_refs_html(refs_html_path, refIDs):
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
        print >>fo, '<p><span style="text-decoration: underline">%s</span>'\
                    '<br/>%s</p>' % (unicode(refID).encode('utf-8'),
                    unicode(source.html(sublist=True)).encode('utf-8'))
    print >>fo, '<div>'
    print >>fo, '</body></html>'
    fo.close()

def write_refs_bibtex(refs_bib_path, refIDs):

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

