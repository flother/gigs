import datetime

from django.contrib.syndication.feeds import Feed
from django.contrib.syndication.views import feed
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed

from gigs.models import Gig, Artist, Venue


class LatestGigs(Feed):

    """Feed class to represent the ten most recently created gigs."""

    feed_type = Atom1Feed
    title = 'Latest gigs from Ripped Records'
    description = 'The most recently added gigs on the Ripped Records site.'
    author_name = 'Ripped Records'

    def link(self):
        """Return the feed's link."""
        return reverse('django.contrib.syndication.views.feed',
            args=('latest-gigs',))

    def items(self):
        """
        Return the ten most recently created gigs that have yet to take
        place.
        """
        return Gig.objects.upcoming().order_by('-created').select_related()[:10]

    def item_link(self, item):
        """Takes a gig as returned by items() and returns its short URL."""
        return item.get_short_absolute_url()

    def item_pubdate(self, item):
        """
        Takes an item, as returned by items(), and returns the item's
        created date for use as its pubdate.
        """
        return item.created


class ArtistGigFeed(Feed):

    """Feed class to represent each indivdual artist."""

    feed_type = Atom1Feed
    author_name = 'Ripped Records'
    description_template = "feeds/gig_description.html"

    def get_object(self, params):
        """
        Return the artist that matches the given slug.
        """
        if len(params) != 1:
            raise Http404
        return get_object_or_404(Artist.objects.select_related(),
            slug=params[0])

    def title(self, obj):
        return "%s's gigs in Edinburgh and Glasgow" % obj.name

    def link(self, obj):
        return reverse(feed, kwargs={"url": "artists/%s" % obj.slug})

    def description(self, obj):
        return "Gigs played by %s in Edinburgh and Glasgow, Scotland" % obj.name

    def items(self, obj):
        """
        Return a list of all published gigs for the artist.
        """
        return obj.gig_set.published(date__gte=datetime.date.today())

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.created


class VenueGigFeed(Feed):

    """Feed class to represent each indivdual venue."""

    feed_type = Atom1Feed
    author_name = 'Ripped Records'
    description_template = "feeds/gig_description.html"

    def get_object(self, params):
        """
        Return the venue that matches the given slug.
        """
        if len(params) != 1:
            raise Http404
        return get_object_or_404(Venue.objects.select_related(),
            slug=params[0])

    def title(self, obj):
        return "%s's gigs in Edinburgh and Glasgow" % obj.name

    def link(self, obj):
        return reverse(feed, kwargs={"url": "venues/%s" % obj.slug})

    def description(self, obj):
        return "Gigs happening at %s, %s" % (obj.name, obj.town)

    def items(self, obj):
        """
        Return a list of all published gigs for the venue.
        """
        return obj.gig_set.published(date__gte=datetime.date.today())

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.created
