from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'HITRAN.views.home', name='home'),
    url(r'^$', 'hitranmeta.views.index'),
    url(r'^news/$', 'hitranmeta.views.news'),
    url(r'^lbl/$', 'HITRAN.hitranlbl.views.index'),
    url(r'^cia/$', 'HITRAN.hitrancia.views.index'),
    url(r'^xsc/$', 'HITRAN.hitranxsc.views.index'),
    url(r'^xsc/(?P<iruv>ir|uv)$', 'HITRAN.hitranxsc.views.index'),
    url(r'^additional/$', 'hitranmeta.views.additional'),

    (r'^tap/sync[/]?$', 'HITRAN.hitranlbl.node_views.sync'),
    (r'^tap/availability[/]?$', 'HITRAN.hitranlbl.node_views.availability'),
    (r'^tap/capabilities[/]?$', 'HITRAN.hitranlbl.node_views.capabilities'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^lbl/results/(?P<path>.*)$',
        'django.views.static.serve', {'document_root': settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^cia/results/(?P<path>.*.tgz)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^cia/results/(?P<path>.*.xsams)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^cia/results/(?P<path>.*)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH + '/cia',
        }),
    )
    urlpatterns += patterns('',
        url(r'^xsc/results/(?P<path>.*.tgz)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^xsc/results/(?P<path>.*.xsams)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^xsc/results/(?P<path>.*)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH + '/xsc',
        }),
    )
    
