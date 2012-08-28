# -*- coding: utf-8 -*-

from search_par import do_search_par
from search_min import do_search_min
from search_atmos_min import do_search_atmos_min
from search_comprehensive import do_search_comprehensive

def do_search(form, output_collections):
    """
    Do the search, using the search parameters parsed in the form instance
    of the LblSearchForm class.

    """
    from django import db
    from django.db import connection
    db.reset_queries()

    output_collection = output_collections[form.output_collection_index]

    return search_routines[output_collection.name](form)

search_routines = {
        'HITRAN2004+': do_search_par,
        'min': do_search_min,
        'atmos-min': do_search_atmos_min,
        'comprehensive': do_search_comprehensive,
}
