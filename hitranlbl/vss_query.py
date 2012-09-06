# -*- coding: utf-8 -*-
# vss_query.py
# Defines the class VSSQuery, representing a query made of the database
# in the VSS query language, a subset of SQL.

from caseless_dict import CaselessDict
from string import lower
from datetime import date
import sqlparse
import logging
log = logging.getLogger('vamdc.hitran_node')
from tap_utils import get_base_URL
from vamdc_standards import REQUESTABLES
from dictionaries import restrictable_types
from hitranmeta.models import Iso
from xsams_queries import get_xsams_src_query, get_xsams_states_query,\
                          get_xsams_trans_query

class VSSQuery(object):
    """
    A class representing the VSS query, with methods to parse and validate it.

    """

    def __init__(self, request):
        self.is_valid = True
        self.error_message = ''
        try:
            self.request = CaselessDict(dict(request.REQUEST))
        except Exception, e:
            self.is_valid = False
            self.error_message = 'Failed to read argument dictionary: %s' % e
            log.error(self.error_message)
        if self.is_valid:
            self.parse_query()
        self.full_url = '%ssync?%s' % (get_base_URL(request),
                                       request.META.get('QUERY_STRING'))

    def parse_query(self):
        """ Parse and validate the query as VSS2. """

        error_list = []

        # check LANG=VSS2
        try:
            self.lang = lower(self.request['LANG'])
        except:
            error_list.append('Couldn\'t find LANG in request')
        else:
            if self.lang != 'vss2':
                error_list.append('Only LANG=VSS2 is supported')
        # get the QUERY string
        try:
            self.query = self.request['QUERY']
        except:
            error_list.append('Couldn\'t find QUERY in request')
        # get the FORMAT
        try:
            self.format = lower(self.request['FORMAT'])
        except:
            error_list.append('Couldn\'t find FORMAT in request')
        else:
            if self.format not in ('xsams', 'par'):
                error_list.append('Only XSAMS and PAR formats are supported')
        # parse the query
        try:
            self.parsed_sql = sqlparse.SQL.parseString(self.query,
                                                       parseAll=True)
        except:
            # we failed to parse the query: bail with extreme prejudice
            error_list.append('Couldn\'t parse the QUERY string: %s'
                                     % self.query)
            self.error_message = '\n'.join(error_list)
            self.is_valid = False
            return

        self.requestables = set()
        self.where = self.parsed_sql.where
        if self.parsed_sql.columns not in ('*', 'ALL'):
            for requested in self.parsed_sql.columns:
                requested = lower(requested)
                if requested not in REQUESTABLES:
                    self.error_list.append(
                        'Unsupported or unknown REQUESTABLE: %s' % requested)
                else:
                    self.requestables.add(requested)

            if 'processes' in self.requestables:
                self.requestables.add('radiativetransitions')
            # always return sources
            self.requestables.add('sources')

        if error_list:
            # validation failed
            self.error_message = '\n'.join(error_list)
            self.is_valid = False

    def __str__(self):
        """ Return a string representation of the query. """
        return self.query

    def make_sql_queries(self):
        """
        Turn the VSS query into a series of SQL queries on the database.
        The returned queries are in a dictionary, keyed by 'src_query',
        'st_query', 't_query' for the sources query, the states query, and
        the transitions query respectively.

        """

        if not self.where:
            return {}

        # parse the where clause into restrictions, joined by logic:
        logic, restrictions, count = sqlparse.splitWhere(self.where)
        # logic is e.g. ['r0', 'and', 'r1', 'and', '(', 'r2', 'or', 'r3', ')']
        # restrictions is a dictionary, keyed by '0', '1', ..., e.g.
        # {'1': ['RadTransWavenumber', '<', '6100.'],
        #  '0': ['RadTransWavenumber', '>', '5000.'],
        #  '2': ['MoleculeChemicalName', 'in', '(', "'H2O'", "'Ammonia'", ')']
        #  ... }
        node_restrictions = {}
        for ri in restrictions:
            restrictable, op, s_rvals = (restrictions[ri][0],
                                         restrictions[ri][1],
                                         restrictions[ri][2:])
            # refer to all restrictables in lower case from here
            restrictable = restrictable.lower()
            if op not in sqlparse.OPTRANS.keys():
                raise Exception('Illegal or unsupported operator in'
                                ' restriction: %s' % op)
            try:
                restrictable_type = restrictable_types[restrictable]
            except KeyError:
                raise Exception('Unknown RESTRICTABLE: %s' % restrictable)
            try:
                self.check_rvals_type(s_rvals, restrictable_type)
            except:
                raise Exception('Invalid value for restrictable %s: %s'
                                % (restrictable, s_rvals))

            # translate the VAMDC restrictable keywords into the
            # appropriate of the hitranlbl_trans table in the HITRAN database
            # the hitranlbl_trans table must be aliased to 't'. Note that
            # node_restrictions[2] is *always a list*, unlike
            # restrictions[ri][2]
            if restrictable == 'radtranswavenumber':
                node_restrictions['r%s' % ri] = ['t.nu', op] + [s_rvals,]
            elif restrictable == 'radtranswavelength':
                op, s_nus = self.lambda_to_nu(op, s_rvals)
                node_restrictions['r%s' % ri] = ['t.nu', op] + [s_nus,]
            elif restrictable == 'radtransprobability':
                node_restrictions['r%s' % ri] = ['t.A', op] + [s_rvals,]
            elif restrictable in ('inchikey', 'moleculeinchikey'):
                op, s_iso_ids = self.get_isos_from_other(op, s_rvals,
                                                 self.iso_from_inchikey)
                node_restrictions['r%s' % ri] = 't.iso_id', op, s_iso_ids
            elif restrictable == 'moleculestoichiometricformula':
                op, s_iso_ids = self.get_isos_from_other(op, s_rvals,
                                                 self.iso_from_molec_stoich)
                node_restrictions['r%s' % ri] = 't.iso_id', op, s_iso_ids
            elif restrictable == 'moleculechemicalname':
                op, s_iso_ids = self.get_isos_from_other(op, s_rvals,
                                                 self.iso_from_molec_name)
                node_restrictions['r%s' % ri] = 't.iso_id', op, s_iso_ids
            else:
                raise Exception('Unsupported or invalid restrictable keyword:'
                                ' %s' % restrictable)

        # add restrictions on valid_to, valid_from dates:
        # XXX Hard-code these to the current date, because there's currently
        # no keyword (is there?) for valid_on date in the VAMDC standards.
        today = date.today().strftime('%Y-%m-%d')
        logic.extend(['and', 'r_valid_from', 'and', 'r_valid_to'])
        node_restrictions['r_valid_from'] = ['t.valid_from','<=', [today,]]
        node_restrictions['r_valid_to'] = ['t.valid_to','>', [today,]]

        q_where = []
        for x in logic:
            if x in node_restrictions.keys():
                q_where.append(self.make_sql_restriction(node_restrictions[x]))
            else:
                q_where.append(x)
        q_where = ' '.join(q_where)
        print q_where

        queries = {'src_query': get_xsams_src_query,
                   'st_query': get_xsams_states_query,
                   't_query': get_xsams_trans_query}
        return queries

    def make_sql_restriction(self, node_restriction):
        """
        Turn the node_restriction, a tuple of (field, operator, values) into
        a valid SQL restriction.

        """

        print 'XXX:', node_restriction
        name, op, args = node_restriction

        if len(args) > 1:
            s_val = '(%s)' % ', '.join(args)
        else:
            s_val = args[0]
        return '%s %s %s' % (name, op, s_val)
        
    def lambda_to_nu(self, op, lambdas):
        nu_list = []
        has_parentheses = False
        if lambdas[0] == '(' and lambdas[-1] == ')':
            has_parentheses = True
        for lamda in lambdas:
            if lamda in ('(', ')'):
                continue
            try:
                nu = 1./float(lamda)
            except ZeroDivisionError:
                # set nu to something huge if lambda = 0
                nu = 1.e20
            nu_list.append(str(nu))
        
        op = sqlparse.reverse_op(op)

        if not has_parentheses:
            if len(nu_list) > 1:
                raise Exception('Invalid argument to RadTransWavelength: %s'
                                % lambdas)
            else:
                return op, nu_list
        #return op, '(%s)' % (', '.join(nu_list),)
        ret_dict = ['(',]
        ret_dict.extend(nu_list)
        ret_dict.append(')')
        return op, ret_dict

    def iso_from_inchikey(self, inchikey):
        return Iso.objects.filter(InChIKey=
                    inchikey).values_list('id', flat=True)

    def iso_from_molec_stoich(self, stoichiometric_formula):
        return Iso.objects.filter(molecule__stoichiometric_formula=
                    stoichiometric_formula).values_list('id', flat=True)

    def iso_from_molec_name(self, name):
        return Iso.objects.filter(molecule__moleculename__name=
                    name).values_list('id', flat=True)

    def get_isos_from_other(self, op, s_rvals, isos_get_method):
        """
        Return a string of requested isotopologue IDs corresponding to the
        requested list of s_rvals, using the method specified by
        isos_get_method.

        """
        iso_ids = []
        has_parentheses = False
        if s_rvals[0] == '(' and s_rvals[-1] == ')':
            has_parentheses = True
        for s_rval in s_rvals:
            s_rval = s_rval.strip('"\'')    # strip all outside quotes, " and '
            if s_rval in ('(', ')'):
                continue
            iso_id_list = isos_get_method(s_rval)
            iso_ids.extend([str(iso_id) for iso_id in iso_id_list])
        if not iso_ids:
            # we didn't find any isotopologues matching the requested InChIKeys
            return op, ['(-1)',]
        if not has_parentheses:
            if len(iso_ids) > 1:
                # a single e.g. molecular stoichiometric formula maps to more
                # than one isotopologue, so generalise the operator
                if op == '=':
                    op = 'in'
                elif op == '<>':
                    op = 'not in'
            else:
                return op, iso_ids
        return op, iso_ids

    def check_rvals_type(self, s_rvals, rtype):
        """
        Check that s_rvals corresponds to a list of strings which can be
        legitimately cast into their correct types.

        """

        if rtype == str:
            # s_rvals is already a list of strings!
            return
        for s_rval in s_rvals:
            if s_rval in ('(', ')'):
                # skip the parentheses
                continue
            try:
                rval = rtype(s_rval)
            except:
                raise
