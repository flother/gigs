from django.conf.urls.defaults import patterns, url

from gigs import views


urlpatterns = patterns('',
    url(r'^$', views.home_page, name='gigs_home_page'),
    url(r'^artists/$', views.artist_list, name='gigs_artist_list'),
    url(r'^venues/$', views.venue_list, name='gigs_venue_list'),
)
