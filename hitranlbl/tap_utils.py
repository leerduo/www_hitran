# -*- coding: utf-8 -*-
# tap_utils.py
# Some helper methods for dealing with TAP queries.
from django.conf import settings
from django.template import Context, loader
from django.http import HttpResponse
from caseless_dict import CaselessDict

def throw_404(request):
    """ Turn a 404 (Not Found) into a TAP error document. """

    text = 'Resource not found: %s' % request.path
    document = loader.get_template('tap/TAP-error-document.xml').render(
                            Context({'error_message_text': text}))
    return HttpResponse(document, status=404, mimetype='text/xml')

def throw_500(request=None, status=500, error_message=''):
    """ Turn a 500 (Internal Server Error) into a TAP error document. """

    error_text = 'Error in TAP service: %s' % error_message
    document = loader.get_template('tap/TAP-error-document.xml').render(
                            Context({'error_message_text' : error_text}))
    return HttpResponse(document, status=status, mimetype='text/xml')

def get_base_URL(request):
    # XXX what the hell does this do?
    return getattr(settings, 'DEPLOY_URL', None) or \
        'http://%s%s/tap/' % (request.get_host(),
                              request.path.split('/tap',1)[0])

def add_headers(headers, response):
    headers = CaselessDict(headers)
    for header in HEADERS:
        if headers.has_key(header):
            response['VAMDC-%s' % header] = headers[header]
    return response

def dquote(s):
    """ Return the string s, surrounded by double quotes. """
    return '"%s"' % s
