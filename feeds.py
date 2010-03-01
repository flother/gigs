from django.contrib.syndication.feeds import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed

from gigs.models import Gig


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

    def item_link(self):
        """
        Return an individual item's link.  Currently not implemented while
        the ``Gig`` model is missing a ``get_absolute_url()`` method.
        """
        return '/'

    def items(self):
        """Return the ten most recently created gigs."""
        return Gig.objects.published().order_by('-created').select_related()[:10]

    def item_pubdate(self, item):
        """
        Takes an item, as returned by items(), and returns the item's
        created date for use as its pubdate.
        """
        return item.created
