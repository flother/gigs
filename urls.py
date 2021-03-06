from django.conf.urls.defaults import patterns, url
from django.views.generic.date_based import archive_year, archive_month,\
    archive_day
from django.views.generic.list_detail import object_list, object_detail

from gigs.feeds import LatestGigs, ArtistGigFeed, VenueGigFeed, TownGigFeed
from gigs.models import Gig, Artist, Town, Promoter
from gigs.sitemaps import GigSitemap, ArtistSitemap, VenueSitemap, TownSitemap,\
    PromoterSitemap
from gigs import views


sitemaps = {
    'gigs': GigSitemap,
    'artists': ArtistSitemap,
    'venues': VenueSitemap,
    'towns': TownSitemap,
    'promoter': PromoterSitemap,
}

feeds = {
    'latest-gigs': LatestGigs,
    'artists': ArtistGigFeed,
    'venues': VenueGigFeed,
    'towns': TownGigFeed,
}


gig_archive_dict = {
    'queryset': Gig.objects.published(),
    'date_field': 'date',
    'template_object_name': 'gig',
    'allow_future': True,
}
gig_archive_year_dict = {'make_object_list': True}
gig_archive_year_dict.update(gig_archive_dict)
gig_archive_month_and_day_dict = {'month_format': '%m'}
gig_archive_month_and_day_dict.update(gig_archive_dict)
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
    url(r'^gigs/$', views.gigs_archive, name='gigs_gig_archive'),
    url(r'^gigs/(?P<year>\d{4})/$', archive_year, gig_archive_year_dict,
        name='gigs_gig_archive_year'),
    url(r'^gigs/(?P<year>\d{4})/(?P<month>\d{2})/$', archive_month,
        gig_archive_month_and_day_dict, name='gigs_gig_archive_month'),
    url(r'^gigs/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$', archive_day,
        gig_archive_month_and_day_dict, name='gigs_gig_archive_day'),
    url(r'^gigs/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>.+)/$',
        views.gig_detail, name='gigs_gig_detail'),
    url(r'^g/(?P<base32_id>\w+)/$', views.gig_detail_shorturl,
        name='gigs_gig_detail_shorturl'),
    url(r'^artists/$', views.artist_list, name='gigs_artist_list'),
    url(r'^artists/(?P<slug>.+)/$', views.artist_detail,
        name='gigs_artist_detail'),
    url(r'^venues/$', views.venue_list, name='gigs_venue_list'),
    url(r'^venues/(?P<slug>.+)/$', views.venue_detail,
        name='gigs_venue_detail'),
    url(r'^towns/$', object_list, town_list_dict, name='gigs_town_list'),
    url(r'^town/(?P<slug>.+)/$', object_detail, {
        'queryset': Town.objects.published(),
        'template_object_name': 'town'}, name='gigs_town_detail'),
    url(r'^promoters/$', object_list, promoter_list_dict,
        name='gigs_promoter_list'),
    url(r'^promoters/(?P<slug>.+)/$', object_detail, {
        'queryset': Promoter.objects.published(),
        'template_object_name': 'promoter'}, name='gigs_promoter_detail'),
    (r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='gigs_feeds'),
)
