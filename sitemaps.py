from django.contrib.sitemaps import Sitemap

from gigs.models import Gig, Artist, Venue, Town, Promoter


class GigSitemap(Sitemap):

    """A Django Sitemap class for the Gig model."""

    changefreq = "monthly"

    def items(self):
        return Gig.objects.published()

    def lastmod(self, obj):
        return obj.updated


class ArtistSitemap(Sitemap):

    """A Django Sitemap class for the Artist model."""

    changefreq = "monthly"

    def items(self):
        return Artist.objects.published()

    def lastmod(self, obj):
        return obj.updated


class VenueSitemap(Sitemap):

    """A Django Sitemap class for the Venue model."""

    changefreq = "weekly"

    def items(self):
        return Venue.objects.published()

    def lastmod(self, obj):
        return obj.updated


class TownSitemap(Sitemap):

    """A Django Sitemap class for the Town model."""

    changefreq = "weekly"

    def items(self):
        return Town.objects.published()

    def lastmod(self, obj):
        return obj.updated


class PromoterSitemap(Sitemap):

    """A Django Sitemap class for the Promoter model."""

    changefreq = "monthly"

    def items(self):
        return Promoter.objects.published()

    def lastmod(self, obj):
        return obj.updated
