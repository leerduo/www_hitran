# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
import os
import sys
import time
import datetime
import logging
log = logging.getLogger('vamdc.hitran_node')
from caseless_dict import CaselessDict
from vamdc_standards import HEADERS, REQUESTABLES, STANDARDS_VERSION
from tap_utils import throw_500, get_base_URL
from vss_query import VSSQuery
import dictionaries
from search_xsams import get_src_ids, xsams_generator, get_transitions_count,\
                         get_isos_count
from search_utils import get_all_source_ids
from hitranmeta.models import Source

NODEID = settings.NODEID

def add_headers(headers, response):
    """
    Attach the headers in the dictionary headers to the response object
    and return it.

    """

    for header_name in headers:
        response['VAMDC-%s' % header_name] = headers[header_name]
    return response

def sync(request):
    """
    Handle a synchronous query on the database made by posting a VSS
    query to the VAMDC HITRAN node url. After verifying the query is
    well-formed, a generator for the XSAMS document is set up and passed
    to HttpResponse as an attachment for the user to download. Headers
    including some meta-data relating to the query results are added to
    the response object.

    """

    log.info('Request from %s: %s' % (request.META['REMOTE_ADDR'],
                                      request.REQUEST))
    vss_query = VSSQuery(request)
    if not vss_query.is_valid:
        error_message = 'Invalid VSS query: %s' % vss_query.error_message
        log.error(error_message)
        return throw_500(status=400, error_message=error_message)

    # translate the VSS query into a series of SQL queries on the
    # database tables:
    try:
        sql_queries = vss_query.make_sql_queries()
    except Exception, e:
        error_message = 'Failed to process VSS query into SQL: %s' % e
        log.debug(error_message)
        return throw_500(status=400, error_message=error_message)

    if not sql_queries:
        log.info('I got nothing back from make_sql_queries(). Returning 204.')
        return HttpResponse('', status=204)

    # fetch the sources before starting the generator, so we can
    # populate the COUNT-SOURCES header
    source_ids = get_src_ids(sql_queries['src_query'])
    # we need all the source_ids, even those belonging to sources cited
    # within notes, etc.
    all_source_ids = get_all_source_ids(source_ids)
    all_sources = Source.objects.filter(pk__in=all_source_ids)
    nsources = all_sources.count()
    log.debug('nsources = %d' % nsources)
    ntrans = get_transitions_count(sql_queries['tc_query'])
    log.debug('ntrans = %d' % ntrans)
    # if the query results have been truncated, calculate a percentage
    truncated_percent = None
    if settings.XSAMS_LIMIT and ntrans > settings.XSAMS_LIMIT:
        truncated_percent = float(settings.XSAMS_LIMIT) / ntrans * 100.
        ntrans = settings.XSAMS_LIMIT
        log.debug('truncated_percent = %.1f' % truncated_percent)

    nisos = get_isos_count(sql_queries['ic_query'])

    # fill the headers dictionary with some header info
    headers = {}
    headers['COUNT-SPECIES'] = nisos
    headers['COUNT-MOLECULES'] = nisos
    headers['COUNT-SOURCES'] = nsources
    headers['COUNT-RADIATIVE'] = ntrans
    # rather than counting the states, or pre-fetching them, estimate:
    headers['COUNT-STATES'] = int(0.435 * ntrans)
    if truncated_percent:
        headers['TRUNCATED'] = truncated_percent

    # OK, then - fire up the generator and hand it to HttpResponse: 
    timestamp = datetime.datetime.now().isoformat()
    generator = xsams_generator(sql_queries, timestamp, all_sources)
    response = HttpResponse(generator, 'text/xml')
    response['Content-Disposition'] = 'attachment; filename=%s-%s.%s'\
                % (NODEID, timestamp, vss_query.format)
    # attach headers
    response = add_headers(headers, response)

    return response

def capabilities(request):
    """
    Render the capabilities.xml document providing some information about
    this node and what can be queried at it.

    """
    c = RequestContext(request, {
                    'accessURL': get_base_URL(request),
                    'RESTRICTABLES': dictionaries.RESTRICTABLES,
                    'RETURNABLES': dictionaries.RETURNABLES,
                    'SOFTWARE_VERSION': settings.SOFTWARE_VERSION,
                    'EXAMPLE_QUERIES': dictionaries.EXAMPLE_QUERIES,
                    })
    return render_to_response('tap/capabilities.xml', c, mimetype='text/xml')

def availability(request):
    """
    Render the availability.xml document used to check the node is up
    and running, and providing its URL.

    """
    c = RequestContext(request, {'accessURL': get_base_URL(request)})
    return render_to_response('tap/availability.xml', c, mimetype='text/xml')

