from django.conf.urls import patterns, url, include
from django_options.testapp.app.views import TestView, test_view, decorated_test_view

urlpatterns = patterns('',
    url(r'', include('django_faker.urls')),
    url(r'^$',          TestView.as_view(), name='index'),
    url(r'^test/$',     test_view, name='test-view'),
    url(r'^test_dec/$', decorated_test_view, name='test-decorated-view'),
)