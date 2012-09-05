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

NODEID = settings.NODEID


def sync(request):
    log.info('Request from %s: %s' % (request.META['REMOTE_ADDR'],
                                      request.REQUEST))
    vss_query = VSSQuery(request)
    if not vss_query.is_valid:
        error_message = 'Invalid VSS query: %s' % vss_query.error_message
        log.error(error_message)
        return throw_500(status=400, error_message=error_message)

    print 'vss_query is:', vss_query
    print 'vss_query.requestables:', vss_query.requestables
    print 'vss_query.where:', vss_query.where
    print 'vss_query.parsed_sql:', vss_query.parsed_sql
    print 'vss_query.parsed_sql.columns:', vss_query.parsed_sql.columns

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

    c = {'search_summary': 'XSAMS search...'}
    return render_to_response('lbl_searchresults.html', c)

def capabilities(request):
    c = RequestContext(request, {'accessURL': get_base_URL(request),
                                 'RESTRICTABLES': dictionaries.RESTRICTABLES,
                                 'RETURNABLES': dictionaries.RETURNABLES,
                                 'SOFTWARE_VERSION': settings.SOFTWARE_VERSION,
                                # XXX omit EXAMPLE_QUERIES, for now
                                })
    return render_to_reponse('tap/capabilities.xml', c, mimetype='text/xml')

def availability(request):
    c = RequestContext(request, {'accessURL': get_base_URL(request)})
    return render_to_response('tap/availability.xml', c, mimetype='text/xml')

