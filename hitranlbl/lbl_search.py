# -*- coding: utf-8 -*-

from search_par import do_search_par
from search_min import do_search_min
from search_atmos_min import do_search_atmos_min
#from search_comprehensive import do_search_comprehensive
from search_venus import do_search_venus
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
        'min': do_search_min,
        'atmos-min': do_search_atmos_min,
        #'comprehensive': do_search_comprehensive,
        'venus': do_search_venus,
        'XSAMS': do_search_xsams,
}
