from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list

from gigs.feeds import LatestGigs
from gigs.models import Town, Promoter
from gigs import views


feeds = {
    'latest-gigs': LatestGigs,
}


town_list_dict = {
    'queryset': Town.objects.published(),
    'allow_empty': True,
    'template_object_name': 'town',
}
promoter_list_dict = {
    'queryset': Promoter.objects.published(),
    'allow_empty': True,
    'template_object_name': 'promoter',
}


urlpatterns = patterns('',
    url(r'^$', views.home_page, name='gigs_home_page'),
    url(r'^gigs/$', views.gigs_index, name='gigs_gig_index'),
    url(r'^gigs/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>.+)/$',
        views.gig_detail, name='gigs_gig_detail'),
    url(r'^artists/$', views.artist_list, name='gigs_artist_list'),
    url(r'^artists/(?P<slug>.+)/$', views.artist_detail,
        name='gigs_artist_detail'),
    url(r'^venues/$', views.venue_list, name='gigs_venue_list'),
    url(r'^towns/$', object_list, town_list_dict, name='gigs_town_list'),
    url(r'^promoters/$', object_list, promoter_list_dict,
        name='gigs_promoter_list'),
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='gigs_feeds'),
)
