# -*- coding: utf-8 -*-
escape = {
u'Š': r'\v{S}',
u'ł': r'\l',
u'é': r'\'{e}',
u'è': r'\`{e}',
u'ë': r'\"{e}',
u'ï': r'\"{i}',
u'n̄': r'\={n}',
u'ñ': r'\~{n}',
u'ó': r'\'{o}',
u'ò': r'\"{o}',
u'ü': r'\"{u}',
u'ö': r'\"{o}',

}

def latex_escape(s):
    """
    Replace non-ASCII characters with their escaped-versions, in so far as
    they can be identified from the dictionary escape.

    """

    uc = []
    for c in s:
        if ord(c) > 128:
            uc.append(c)
    for c in uc:
        try:
            s = s.replace(c, escape[c])
        except KeyError:
            print 'Warning! unescaped character, %s, in string:\n%s' % (c, s)
    return s
