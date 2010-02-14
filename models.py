import datetime

from django.db import models

from gigs.managers import GigManager


class Gig(models.Model):

    """
    A music gig with one headline act taking place on a specific date at
    a specific venue.
    """

    artist = models.ForeignKey('Artist')
    slug = models.SlugField(unique_for_date=True)
    venue = models.ForeignKey('Venue')
    promoter = models.ForeignKey('Promoter', blank=True, null=True)
    date = models.DateField()
    price = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
        null=True)
    sold_out = models.BooleanField(default=False)
    extra_information = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    published = models.BooleanField(default=True)
    import_identifiers = models.ManyToManyField('ImportIdentifier')

    objects = GigManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('date',)
        unique_together = (('artist', 'venue', 'date'),)

    def __unicode__(self):
        return "%s at %s on %s" % (self.artist, self.venue, self.date)


class Artist(models.Model):

    """A musician, singer, or band."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to='artists', blank=True, null=True)
    web_site = models.URLField(blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier')

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def number_of_upcoming_gigs(self):
        """Return the number of gigs this artist is to play."""
        return self.gig_set.filter(date__gte=datetime.date.today()).count()


class Venue(models.Model):

    """
    A physical location within a specified town or city where a gig takes
    place.
    """

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=128, blank=True)
    town = models.ForeignKey('Town')
    photo = models.ImageField(upload_to='venues', blank=True, null=True)
    web_site = models.URLField(blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier')

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return "%s, %s" % (self.name, self.town)

    def number_of_upcoming_gigs(self):
        """Return the number of gigs this venue is to host."""
        return self.gig_set.filter(date__gte=datetime.date.today()).count()


class Town(models.Model):

    """A town or city."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    photo = models.ImageField(upload_to='towns')
    longitude = models.IntegerField(blank=True, null=True)
    latitude = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier')

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def number_of_upcoming_gigs(self):
        """Return the number of gigs this town is to host."""
        return Gig.objects.published(venue__town=self).count()


class Promoter(models.Model):

    """The company or organisation that organises gigs."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    web_site = models.URLField(blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier')

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def number_of_upcoming_gigs(self):
        """Return the number of gigs this promoter is to promote."""
        return self.gig_set.filter(date__gte=datetime.date.today()).count()


class ImportIdentifier(models.Model):

    """
    An unique identifier for an artist, venue, town, or promoter used when
    importing data from Ripping Records.

    This is used because the Ripping Records page will often use different
    spellings (or misspell) the names of artists or venues especially.  But
    instead of needing multiple database rows for the same object, this
    identifier is used to link the many spellings to one model object.
    """

    identifier = models.CharField(max_length=128)

    def __unicode__(self):
        return self.identifier