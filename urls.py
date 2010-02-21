from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list

from gigs.models import Town, Promoter
from gigs import views


town_list_dict = {
    'queryset': Town.objects.all(),
    'allow_empty': True,
    'template_object_name': 'town',
}
promoter_list_dict = {
    'queryset': Promoter.objects.all(),
    'allow_empty': True,
    'template_object_name': 'promoter',
}


urlpatterns = patterns('',
    url(r'^$', views.home_page, name='gigs_home_page'),
    url(r'^artists/$', views.artist_list, name='gigs_artist_list'),
    url(r'^venues/$', views.venue_list, name='gigs_venue_list'),
    url(r'^towns/$', object_list, town_list_dict, name='gigs_town_list'),
    url(r'^promoters/$', object_list, promoter_list_dict,
        name='gigs_promoter_list'),
)
