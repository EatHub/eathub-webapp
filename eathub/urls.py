# coding=utf-8
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings
from rest_framework import viewsets, routers
from webapp.models import Recipe

admin.autodiscover()

handler500 = 'webapp.views.handle500'

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'eathub.views.home', name='home'),
    # url(r'^eathub/', include('eathub.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),

    url(r'^', include('webapp.urls')),
    url(r'^ajax/', include('ajax.urls')),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^password/', include('password_reset.urls')),
    url(r'^api/', include('api.urls')),

)


# Solución a los estáticos en Heroku
# Mil gracias: http://stackoverflow.com/questions/9047054/heroku-handling-static-files-in-django-app
# if settings.DEBUG ??
urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
