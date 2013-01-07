from django.conf.urls import patterns, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()


urlpatterns = patterns('',
#    url(r'^admin/options/(?P<page_code>.*)/$', option_pages.as_view(), name='admin-options-page'),
#    (r'^admin/options/', include('django_options.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}),
    (r'', include('app.urls')),

)



# ... the rest of your URLconf goes here ...

urlpatterns += staticfiles_urlpatterns()

