# -*- coding: utf-8 -*-

from search_par import do_search_par
from search_astrophysics import do_search_astrophysics
from search_atmospheric import do_search_atmospheric
from search_atmospheric_min import do_search_atmospheric_min
#from search_comprehensive import do_search_comprehensive
from search_venus import do_search_venus
from search_CO_test import do_search_CO_test
from search_xsams import do_search_xsams

def do_search(form, output_collections):
    """
    Do the search, using the search parameters parsed in the form instance
    of the LblSearchForm class.

    """

    output_collection = output_collections[form.output_collection_index]
    return search_routines[output_collection.name](form)

# The search_routines dictionary maps the names of the output "collections"
# onto the methods which implement them - don't forget to import them at the
# top of this file!
search_routines = {
        'HITRAN2004+': do_search_par,
        'astrophysics': do_search_astrophysics,
        'atmospheric': do_search_atmospheric,
        'atmospheric-min': do_search_atmospheric_min,
        #'comprehensive': do_search_comprehensive,
        'venus': do_search_venus,
        'XSAMS': do_search_xsams,
        'CO-test': do_search_CO_test,
}
