# -*- coding: utf-8 -*-
# xsams_queries.py
# Make the SQL queries on the tables of the HITRAN database for output
# in XSAMS format.
from django.conf import settings

def get_limit_query():
    """
    The LIMIT clause, if we're limiting the number of transitions to
    return.

    """
    limit_query = ''
    if settings.XSAMS_LIMIT is not None:
        limit_query = ' LIMIT %d' % settings.XSAMS_LIMIT
    return limit_query

def get_xsams_src_query(q_subwhere, prm_names):
    """
    Make and return the SQL query for the source IDs of parameters to be
    returned by the query, which will be written to the XSAMS output format.

    Arguments:
    q_subwhere: the main "WHERE" clause on the hitranlbl_trans table,
    representing the restrictions on the search
    prm_names: a list of the names of the parameters that will be searched
    for - these tables will be joined to hitranlbl_trans in the SQL query

    """

    limit_query = get_limit_query()
    sub_queries = []
    for prm_name in prm_names:
        if prm_name == 'A':
            # the source for A is always the same as that for Sw, so skip
            continue
        sub_queries.append(
                'SELECT DISTINCT(p_%s.source_id) AS src_id'
                ' FROM hitranlbl_trans t, prm_%s p_%s WHERE %s AND'
                ' p_%s.trans_id=t.id%s' % (prm_name, prm_name, prm_name,
                                           q_subwhere, prm_name, limit_query)
                          )
    src_query = ['SELECT DISTINCT(src_id) FROM (',]
    src_query.append(' UNION '.join(sub_queries))
    src_query.append(') x')  # "Every derived table must have its own alias"
    return ''.join(src_query)

def get_xsams_states_query(q_subwhere):
    """
    Make and return the SQL query for the states to be returned by the query,
    which will be written to the XSAMS output format.

    Arguments:
    q_subwhere: the main "WHERE" clause on the hitranlbl_trans table,
    representing the restrictions on the search

    """

    limit_query = get_limit_query()
    if settings.XSAMS_LIMIT is not None:
        limit_query = ' LIMIT %d' % settings.XSAMS_LIMIT
    sub_queryp = 'SELECT DISTINCT(statep_id) AS sid FROM hitranlbl_trans t'\
                 ' WHERE %s%s' % (q_subwhere, limit_query)
    sub_querypp = 'SELECT DISTINCT(statepp_id) AS sid FROM hitranlbl_trans t'\
                 ' WHERE %s%s' % (q_subwhere, limit_query)
    
    st_query = 'SELECT st.iso_id, st.id, st.energy, st.g, st.nucspin_label,'\
          ' st.qns_xml FROM hitranlbl_state st, (SELECT DISTINCT(sid)'\
          ' FROM (%s UNION %s) sids, hitranlbl_state s WHERE sids.sid=s.id)'\
          ' qst WHERE st.id=sid ORDER BY st.iso_id' % (sub_queryp, sub_querypp)
    return st_query

def get_xsams_trans_query(q_subwhere, prm_names):
    """
    Make and return the SQL query for the states to be returned by the query,
    which will be written to the XSAMS output format.

    Arguments:
    q_subwhere: the main "WHERE" clause on the hitranlbl_trans table,
    representing the restrictions on the search
    prm_names: a list of the names of the parameters that will be searched
    for - these tables will be joined to hitranlbl_trans in the SQL query

    """

    limit_query = get_limit_query()
    # the fields to return from the query
    q_fields = ['t.iso_id','t.id',  't.statep_id', 't.statepp_id',
                't.multipole']
    for prm_name in prm_names:
        q_fields.extend(['p_%s.val' % prm_name, 'p_%s.err' % prm_name,
                         'p_%s.source_id' % prm_name])
    # the table joins
    q_from_list = ['hitranlbl_trans t',]
    for prm_name in prm_names:
        q_from_list.append('prm_%s p_%s ON p_%s.trans_id=t.id' % (prm_name,
                           prm_name, prm_name))
    q_from = ' LEFT OUTER JOIN '.join(q_from_list)

    t_query = 'SELECT %s FROM %s WHERE %s%s'\
                 % (', '.join(q_fields), q_from, q_subwhere, limit_query)
    return t_query
