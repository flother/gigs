import base64
import datetime
import hashlib
import os
import unicodedata
import urllib2

from django.conf import settings
from django.db import models
from django.db.models import Count, permalink
from django.db.models.signals import post_save
from django.utils.dateformat import format
from django.utils.html import strip_tags, urlize
from markdown import markdown
try:
    from musicbrainz2.webservice import Query, ReleaseFilter, Release,\
        ArtistFilter
except ImportError:
    pass
try:
    import pylast
except ImportError:
    pass

from gigs.managers import PublishedManager, GigManager


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
    cancelled = models.BooleanField(default=False)
    extra_information = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.GIG_IMPORT_TYPE})

    objects = GigManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('date', 'artist__slug')
        unique_together = (('artist', 'venue', 'date'),)

    def __unicode__(self):
        return "%s at %s on %s" % (self.artist, self.venue,
            format(self.date, settings.DATE_FORMAT))

    @permalink
    def get_absolute_url(self):
        """Return the absolute URL for a gig."""
        from gigs.views import gig_detail
        kwargs = {
            'year': self.date.strftime('%Y'),
            'month': self.date.strftime('%m'),
            'day': self.date.strftime('%d'),
            'slug': self.slug,
        }
        return (gig_detail, None, kwargs)

    @permalink
    def get_short_absolute_url(self):
        """
        Return a shorter version of the gig's absolute URL, with the id in
        base 32 used as the unique identifier.
        """
        from gigs.views import gig_detail_shorturl
        base32_id = base64.b32encode(str(self.pk)).strip('=').lower()
        return (gig_detail_shorturl, None, {'base32_id': base32_id})

    def is_finished(self):
        """Return True if the gig date has passed, False otherwise."""
        return self.date < datetime.date.today()

    def similar_upcoming_gigs(self):
        """
        Return a list of upcoming gigs similar to this one, based on
        artist similarity.  The list is ordered soonest first.
        """
        similar_gig_ids = sum([[g["id"] for g in
            a.gig_set.upcoming().values("id")] for a in
            self.artist.similar_artists.published()], [])
        return Gig.objects.filter(id__in=similar_gig_ids).order_by("date")


class Artist(models.Model):

    """A musician, singer, or band."""

    PHOTO_UPLOAD_DIRECTORY = 'gigs/img/artists'

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    biography = models.TextField(blank=True)
    biography_html = models.TextField(blank=True, editable=False)
    photo = models.ImageField(upload_to=PHOTO_UPLOAD_DIRECTORY, blank=True)
    web_site = models.URLField(blank=True)
    similar_artists = models.ManyToManyField("self", symmetrical=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    mbid = models.CharField(verbose_name='MusicBrainz id', max_length=36,
        unique=True)
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.ARTIST_IMPORT_TYPE})

    objects = PublishedManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('slug', 'name')

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        """Return the absolute URL for an artist."""
        return ('gigs_artist_detail', (self.slug,))

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=False):
        """
        Update the ``biography_html`` and ``number_of_upcoming_gigs``
        fields.

        Convert the plain-text ``biography`` field to HTML using Markdown
        and store it in the ``biography_html`` field.

        Update the number of upcoming gigs for this artist.  The update is
        bypassed by default, but can be forced by passing setting the
        third argument, ``update_number_of_upcoming_gigs``, to ``True``.
        The implication is that this should only be updated via the
        ``import_gigs_from_ripping_records`` command.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.upcoming(
                artist__id=self.id).values('artist_id')
            gig_count = upcoming_gigs.annotate(num_of_artists=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_artists')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_artists']
            except IndexError:
                self.number_of_upcoming_gigs = 0  # No gigs yet.
        self.biography_html = markdown(urlize(self.biography, trim_url_limit=40,
            nofollow=False))
        super(Artist, self).save(force_insert, force_update)

    def populate_album_set(self):
        """
        Find and create models for all albums released by this artist.
        Only albums with an Amazon ASIN are imported, to try and stop the
        database getting clogged up with b-sides, remixes, and bonus
        material.
        """
        # We can't do anything without the MusicBrainz and Last.fm libraries.
        try:
            ReleaseFilter
        except NameError:
            return False
        # Find any official album release held by MusicBrainz for this artist.
        filter = ReleaseFilter(artistName=self.name, releaseTypes=(Release.TYPE_ALBUM,
            Release.TYPE_OFFICIAL))
        query = Query()
        releases = query.getReleases(filter)
        for release in releases:
            album = release.release
            # Only import albums with an Amazon ASIN.  That allows for some
            # quality-control as Music Brainz lists every B-side and bonus
            # material you can think of.
            if album.asin:
                # First try and find an already-existing album with this ASIN
                # As an ASIN is unique it means we'll find it even if the fields
                # have been changed since creation.
                try:
                    db_album = Album.objects.get(asin=album.asin)
                except Album.DoesNotExist:
                    db_album = Album(artist=self, title=album.title,
                        asin=album.asin, mbid=album.id.rsplit("/", 1)[1])
                    # MusicBrainz stores releases dates for as many countries as
                    # it can.  I'm only interested in Britain though, so look
                    # for that first.  As a fallback, us the world wide release
                    # date (XE) or the US release date.
                    release_dates = dict((r.country, r.date)
                        for r in album.releaseEvents)
                    if release_dates:
                        # GB = United Kingdom, XE = world, US = United States.
                        for country in ('GB', 'XE', 'US'):
                            if release_dates.has_key(country):
                                db_album.released_in = country
                                # The release date can be in the format "2010",
                                # "2010-02", or "2010-02-18", so make up the
                                # missing month and/or day so a proper release
                                # date object can be created.
                                release_date = release_dates[country]
                                date_list = map(int, release_date.split('-'))
                                try:
                                    db_album.release_date = datetime.date(
                                        *date_list + [1] * (3 - len(date_list)))
                                except ValueError:
                                    pass  # Date couldn't be parsed.
                                break
                    db_album.save()

    def get_photo(self):
        """
        Attempt to find a photo for this artist.  The Last.fm API is used to
        find the primary image.  This requires the pylast module; if it isn't
        found nothing will be done.
        """
        # Make sure the pylast module is available.
        try:
            pylast
        except NameError:
            return False
        # Create a connection to the Last.fm API.
        lastfm = pylast.get_lastfm_network(api_key=settings.LASTFM_API_KEY)
        try:
            lastfm_artist = lastfm.get_artist(self.name)
            lastfm_images = lastfm_artist.get_images()
            primary_image = lastfm_images[0]
            try:
                primary_image_url = primary_image.sizes.original
            except AttributeError:
                primary_image_url = primary_image['sizes']['original']
            # Read the image data from the URL supplied.
            response = urllib2.urlopen(primary_image_url)
            data = response.read()
            # Store the photo on disk.
            filename = os.path.join(settings.MEDIA_ROOT,
                Artist.PHOTO_UPLOAD_DIRECTORY, '%s.jpg' % self.slug)
            fh = open(filename, 'w')
            fh.write(data)
            fh.close()
            # Link the photo to the artist (i.e. save the Artist object).
            self.photo = os.path.join(Artist.PHOTO_UPLOAD_DIRECTORY,
                '%s.jpg' % self.slug)
            self.save()
        except (pylast.WSError, IndexError):
            pass


    def get_biography(self):
        """Import artist briography from Last.fm."""
        # Make sure the pylast module is available.
        try:
            pylast
        except NameError:
            return False
        # Open a connection to the Last.fm API.
        lastfm = pylast.get_lastfm_network(api_key=settings.LASTFM_API_KEY)
        lastfm_artist = lastfm.get_artist(self.name)
        try:
            # Get the biography from Last.fm.
            biography = lastfm_artist.get_bio_content()
            bio_published_date = lastfm_artist.get_bio_published_date()
            if bio_published_date:
                plain_text_biography = strip_tags(biography)
                # If the biography is different to the saved version or the
                # artist biography is blank, save the artist's biography.
                # Note this will overwrite any changes that have been made
                # to the biography via the admin.
                if (not plain_text_biography == self.biography or
                        self.biography == ''):
                    self.biography = plain_text_biography
                    self.save()
        except (pylast.WSError, urllib2.URLError, urllib2.HTTPError):
            # An error occurs if the artist's name has a character in that
            # Last.fm doesn't like, or on the occasional dropped connection.
            pass

    def get_musicbrainz_id(self):
        """
        Retrieve the MusicBrainz id for this artist and save it on the
        model.
        """
        # Make sure the useful bits of the musicbrainz2 package have been
        # imported.
        try:
            Query, ArtistFilter
        except NameError:
            return False
        # Query MusicBrainz.
        artist_filter = ArtistFilter(name="Biffy Clyro")
        query = Query()
        try:
            artist = query.getArtists(artist_filter)[0].artist
            self.mbid = artist.id.rsplit("/", 1)[1]
            self.save()
        except (IndexError, AttributeError):
            return False


class Album(models.Model):

    """A musical release by an artist."""

    PHOTO_UPLOAD_DIRECTORY = 'gigs/img/albums'
    UK_RELEASE_LOCATION = 'GB'
    US_RELEASE_LOCATION = 'US'
    WORLDWIDE_RELEASE_LOCATION = 'XE'
    RELEASE_LOCATIONS = (
        (UK_RELEASE_LOCATION, 'United Kingdom'),
        (US_RELEASE_LOCATION, 'United States'),
        (WORLDWIDE_RELEASE_LOCATION, 'World wide'),
    )

    title = models.CharField(max_length=128)
    artist = models.ForeignKey(Artist)
    cover_art = models.ImageField(upload_to=PHOTO_UPLOAD_DIRECTORY, blank=True)
    release_date_raw = models.CharField(max_length=16, editable=False,
        blank=True)
    release_date = models.DateField(blank=True, null=True)
    released_in = models.CharField(max_length=2, choices=RELEASE_LOCATIONS,
        blank=True)
    asin = models.CharField(verbose_name='ASIN', max_length=16, blank=True)
    mbid = models.CharField(verbose_name='MusicBrainz id', max_length=36,
        unique=True)
    published = models.BooleanField(default=True)

    objects = PublishedManager()

    class Meta:
        ordering = ('artist', '-release_date',)
        unique_together = (('title', 'artist', 'asin'),)

    def __unicode__(self):
        return self.title

    def get_cover_art(self):
        """Attempt to get the album's cover art from Last.fm."""
        try:
            pylast
        except NameError:
            return False
        album_id = unicodedata.normalize('NFKD',
            unicode(' '.join([self.artist.name, self.title]))).encode('ascii',
            'ignore')
        album_hash = hashlib.sha1(album_id).hexdigest()
        lastfm = pylast.get_lastfm_network(api_key=settings.LASTFM_API_KEY)
        lastfm_album = lastfm.get_album(self.artist.name, self.title)
        try:
            cover_image = lastfm_album.get_cover_image()
            response = urllib2.urlopen(cover_image)
            data = response.read()
            # Store the photo on disk and link the photo to the album.
            filename = os.path.join(settings.MEDIA_ROOT,
                Album.PHOTO_UPLOAD_DIRECTORY, '%s.jpg' % album_hash)
            fh = open(filename, 'w')
            fh.write(data)
            fh.close()
            self.cover_art = os.path.join(Album.PHOTO_UPLOAD_DIRECTORY,
                '%s.jpg' % album_hash)
            self.save()
        except (pylast.WSError, AttributeError, urllib2.HTTPError):
            pass


class Venue(models.Model):

    """
    A physical location within a specified town or city where a gig takes
    place.
    """

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True, editable=False)
    address = models.CharField(max_length=128, blank=True)
    town = models.ForeignKey('Town')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    web_site = models.URLField(blank=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.VENUE_IMPORT_TYPE})

    objects = PublishedManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('slug', 'name')

    def __unicode__(self):
        return "%s, %s" % (self.name, self.town)

    @permalink
    def get_absolute_url(self):
        """Return the absolute URL for a venue."""
        return ('gigs_venue_detail', (self.slug,))

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=False):
        """
        Update the ``description_html`` and ``number_of_upcoming_gigs``
        fields.

        Convert the plain-text ``description`` field to HTML using Markdown
        and store it in the ``description_html`` field.

        Update the number of upcoming gigs for this venue.  The update is
        bypassed by default, but can be forced by passing setting the
        third argument, ``update_number_of_upcoming_gigs``, to ``True``.
        The implication is that this should only be updated via the
        ``import_gigs_from_ripping_records`` command.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.upcoming(
                venue__id=self.id).values('venue_id')
            gig_count = upcoming_gigs.annotate(num_of_venues=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_venues')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_venues']
            except IndexError:
                self.number_of_upcoming_gigs = 0  # No gigs yet.
        self.description_html = markdown(urlize(self.description,
            trim_url_limit=40, nofollow=False))
        super(Venue, self).save(force_insert, force_update)


class Town(models.Model):

    """A town or city."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.TOWN_IMPORT_TYPE})

    objects = PublishedManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        """Return the absolute URL for a town."""
        return ('gigs_town_detail', (self.slug,))

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=False):
        """
        Update the number of upcoming gigs in this town.

        The update is bypassed by default but can be forced by setting the
        third argument, ``update_number_of_upcoming_gigs``, to ``True``.
        The implication is that this should only be updated via the
        ``import_gigs_from_ripping_records`` command.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.upcoming(
                venue__town__id=self.id).values('venue__town__id')
            gig_count = upcoming_gigs.annotate(num_of_towns=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_towns')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_towns']
            except IndexError:
                self.number_of_upcoming_gigs = 0  # No gigs yet.
        super(Town, self).save(force_insert, force_update)

    def upcoming_gigs(self):
        """Return a queryset containing all upcoming gigs in this town."""
        return Gig.objects.upcoming(venue__town=self)


class Promoter(models.Model):

    """The company or organisation that organises gigs."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    web_site = models.URLField(blank=True)
    number_of_upcoming_gigs = models.IntegerField(default=0, editable=False)
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    import_identifiers = models.ManyToManyField('ImportIdentifier',
        limit_choices_to={'type': ImportIdentifier.PROMOTER_IMPORT_TYPE})

    objects = PublishedManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ('slug', 'name')

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        """Return the absolute URL for a promoter."""
        return ('gigs_promoter_detail', (self.slug,))

    def save(self, force_insert=False, force_update=False,
        update_number_of_upcoming_gigs=False):
        """
        Update the number of upcoming gigs for this promoters.

        The update is bypassed by default but can be forced by setting
        the third argument, ``update_number_of_upcoming_gigs``, to ``True``.
        The implication is that this should only be updated via the
        ``import_gigs_from_ripping_records`` command.
        """
        if update_number_of_upcoming_gigs:
            upcoming_gigs = Gig.objects.upcoming(
                promoter__id=self.id).values('promoter_id')
            gig_count = upcoming_gigs.annotate(num_of_promoters=Count('id'))
            try:
                ordered_gig_count = gig_count.order_by('-num_of_promoters')[0]
                self.number_of_upcoming_gigs = ordered_gig_count['num_of_promoters']
            except IndexError:
                self.number_of_upcoming_gigs = 0  # No gigs yet.
        super(Promoter, self).save(force_insert, force_update)


def ensure_gig_slug_matches_artist_slug(sender, **kwargs):
    """
    Signal receiver; called once an Artist model is saved.  If any
    upcoming gig for this artist has a slug different to that of the
    artist, the gig's slug is updated to match the artist's.
    """
    artist = kwargs['instance']
    if not kwargs['created']:
        for gig in artist.gig_set.upcoming():
            if gig.slug != artist.slug:
                gig.slug = artist.slug
                gig.save()
post_save.connect(ensure_gig_slug_matches_artist_slug, sender=Artist)


def populate_artist_metadata(sender, **kwargs):
    """
    Signal receiver; called once an Artist model is saved, populating
    the artist's photo and biography if the artist is a new creation.
    """
    if kwargs['created']:
        kwargs['instance'].get_photo()
        kwargs['instance'].get_biography()
        kwargs['instance'].get_musicbrainz_id()
post_save.connect(populate_artist_metadata, sender=Artist)


def populate_artist_album_set(sender, **kwargs):
    """
    Signal receiver; called once an Artist model is saved, populating
    the artist's set of albums if the artist is a new creation.
    """
    if kwargs['created']:
        kwargs['instance'].populate_album_set()
post_save.connect(populate_artist_album_set, sender=Artist)


def get_album_cover_art(sender, **kwargs):
    """
    Signal receiver; called once an Album model is saved, getting the
    album's cover art from Last.fm if it can.
    """
    if kwargs['created']:
        kwargs['instance'].get_cover_art()
post_save.connect(get_album_cover_art, sender=Album)
