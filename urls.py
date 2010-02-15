from django.conf.urls.defaults import patterns, url

from gigs import views


urlpatterns = patterns('',
    url(r'^$', views.home_page, name='gigs_home_page'),
)
