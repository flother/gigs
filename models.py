import datetime

from django.db import models
from django.db.models import Count

from gigs.managers import GigManager


class ImportIdentifier(models.Model):

    """
    An unique identifier for an artist, venue, town, or promoter used when
    importing data from Ripping Records.

    This is used because the Ripping Records page will often use different
    spellings (or misspell) the names of artists or venues especially.  But
    instead of needing multiple database rows for the same object, this
    identifier is used to link the many spellings to one model object.
    """

    GIG_IMPORT_TYPE = 1
    ARTIST_IMPORT_TYPE = 2
    VENUE_IMPORT_TYPE = 3
    TOWN_IMPORT_TYPE = 4
    PROMOTER_IMPORT_TYPE = 5
    IMPORT_TYPES = (
        (GIG_IMPORT_TYPE, 'Gig'),
        (ARTIST_IMPORT_TYPE, 'Artist'),
        (VENUE_IMPORT_TYPE, 'Venue'),
        (TOWN_IMPORT_TYPE, 'Town'),
        (PROMOTER_IMPORT_TYPE, 'Promoter'),
    )

    identifier = models.CharField(max_length=128)
    type = models.IntegerField(choices=IMPORT_TYPES)

    class Meta:
        ordering = ('identifier',)
        unique_together = (('identifier', 'type'),)

    def __unicode__(self):
        return self.identifier


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
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.GIG_IMPORT_TYPE})

    objects = GigManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('date',)
        unique_together = (('artist', 'venue', 'date'),)

    def __unicode__(self):
        return "%s at %s on %s" % (self.artist, self.venue, self.date)


class Artist(models.Model):

    """A musician, singer, or band."""

    PHOTO_UPLOAD_DIRECTORY = 'gigs/img/artists'

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to=PHOTO_UPLOAD_DIRECTORY, blank=True,
        null=True)
    web_site = models.URLField(blank=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.ARTIST_IMPORT_TYPE})

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=True):
        """
        Update the number of upcoming gigs for this artist.

        The update can be bypassed by passing setting the third argument,
        ``update_number_of_upcoming_gigs`` to ``False``.  This is useful
        in the import from Ripping Records so artist objects aren't saved
        over and over, but just once at the end.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.published(artist__id=self.id,
                date__gte=datetime.date.today()).values('artist_id')
            gig_count = upcoming_gigs.annotate(num_of_artists=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_artists')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_artists']
            except IndexError:
                pass  # No gigs yet.
        super(Artist, self).save(force_insert=False, force_update=False)


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
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.VENUE_IMPORT_TYPE})

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return "%s, %s" % (self.name, self.town)

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=True):
        """
        Update the number of upcoming gigs at this venue.

        The update can be bypassed by passing setting the third argument,
        ``update_number_of_upcoming_gigs`` to ``False``.  This is useful
        in the import from Ripping Records so venue objects aren't saved
        over and over, but just once at the end.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.published(venue__id=self.id,
                date__gte=datetime.date.today()).values('venue_id')
            gig_count = upcoming_gigs.annotate(num_of_venues=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_venues')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_venues']
            except IndexError:
                pass  # No gigs yet.
        super(Venue, self).save(force_insert=False, force_update=False)


class Town(models.Model):

    """A town or city."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    photo = models.ImageField(upload_to='towns')
    longitude = models.IntegerField(blank=True, null=True)
    latitude = models.IntegerField(blank=True, null=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.TOWN_IMPORT_TYPE})

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=True):
        """
        Update the number of upcoming gigs in this town.

        The update can be bypassed by passing setting the third argument,
        ``update_number_of_upcoming_gigs`` to ``False``.  This is useful
        in the import from Ripping Records so town objects aren't saved
        over and over, but just once at the end.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.published(venue__town__id=self.id,
                date__gte=datetime.date.today()).values('venue__town__id')
            gig_count = upcoming_gigs.annotate(num_of_towns=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_towns')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_towns']
            except IndexError:
                pass  # No gigs yet.
        super(Town, self).save(force_insert=False, force_update=False)


class Promoter(models.Model):

    """The company or organisation that organises gigs."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    web_site = models.URLField(blank=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.PROMOTER_IMPORT_TYPE})

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=True):
        """
        Update the number of upcoming gigs for this promoters.

        The update can be bypassed by passing setting the third argument,
        ``update_number_of_upcoming_gigs`` to ``False``.  This is useful
        in the import from Ripping Records so promoter objects aren't
        saved over and over, but just once at the end.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.published(promoter__id=self.id,
                date__gte=datetime.date.today()).values('promoter_id')
            gig_count = upcoming_gigs.annotate(num_of_promoters=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_promoters')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_promoters']
            except IndexError:
                pass  # No gigs yet.
        super(Promoter, self).save(force_insert=False, force_update=False)
