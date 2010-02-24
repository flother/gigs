from haystack import indexes
from haystack import site

from gigs.models import Gig, Artist, Venue


class GigIndex(indexes.SearchIndex):
    """Haystack search index for ``gigs.models.Gig``."""
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_queryset(self):
        """Ensure Haystack indexes only published gigs."""
        return Gig.objects.published()


class ArtistIndex(indexes.SearchIndex):
    """Haystack search index for ``gigs.models.Artist``."""
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)


class VenueIndex(indexes.SearchIndex):
    """Haystack search index for ``gigs.models.Venue``."""
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)


site.register(Gig, GigIndex)
site.register(Artist, ArtistIndex)
site.register(Venue, VenueIndex)
