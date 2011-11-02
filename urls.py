from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'HITRAN.views.home', name='home'),
    url(r'^HITRAN/lbl/$', 'HITRAN.hitranlbl.views.index'),
    url(r'^HITRAN/cia/$', 'HITRAN.hitrancia.views.index'),
    url(r'^HITRAN/xsc/$', 'HITRAN.hitranxsc.views.index'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^HITRAN/lbl/results/(?P<path>.*)$',
        'django.views.static.serve', {'document_root': settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^HITRAN/cia/results/(?P<path>.*.tgz)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^HITRAN/cia/results/(?P<path>.*.xsams)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^HITRAN/cia/results/(?P<path>.*)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH + '/cia',
        }),
    )
    urlpatterns += patterns('',
        url(r'^HITRAN/xsc/results/(?P<path>.*.tgz)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^HITRAN/xsc/results/(?P<path>.*.xsams)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH,
        }),
    )
    urlpatterns += patterns('',
        url(r'^HITRAN/xsc/results/(?P<path>.*)$',
        'django.views.static.serve', {'document_root':
                                        settings.RESULTSPATH + '/xsc',
        }),
    )
    
