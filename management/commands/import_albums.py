import datetime
import hashlib
import logging
from optparse import make_option
import os
import sys
import time
import unicodedata
import urllib2

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
try:
    from musicbrainz2.webservice import Query, ReleaseFilter, Release
except ImportError:
    pass
try:
    import pylast
except ImportError:
    pass


from gigs.models import Artist, Album


LOGGING_VERBOSITY = {0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}


class Command(BaseCommand):
    help = "Imports albums from MusicBrainz for all the artists in the database."
    base_options = (
        make_option('-a', '--age', action='store', default=0, type='int',
            help='Import albums only for those artists created within this time period (in hours). Default is all artists.'),
    )
    option_list = BaseCommand.option_list + base_options

    def handle(self, **options):
        """
        Import any albums held in the MusicBrainz database for each artist
        in the database.  Only albums with an Amazon ASIN are imported, to
        try and stop the database getting clogged up with B-sides,
        remixes, and bonus material.
        """
        # Create the logger we'll use to store all the output.
        verbosity = int(options.get('verbosity', 1))
        logger = logging.getLogger('Ripped Records logger')
        logger.setLevel(LOGGING_VERBOSITY[verbosity])
        logger_handler = logging.StreamHandler()
        logger_formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        logger_handler.setFormatter(logger_formatter)
        logger.addHandler(logger_handler)
        logger.info('Importing albums.')

        # Make sure the musicbrainz2 module is available.
        try:
            ReleaseFilter
        except NameError:
            logger.critical('You need to install the musicbrainz2 module.')
            sys.exit(1)
        # Make sure the pylast module is available.
        try:
            pylast
        except NameError:
            logger.critical('You need to install the pylast module.')
            sys.exit(1)

        # Find the age limit for artists.
        age = options.get('age', 0)
        earliest_date = datetime.datetime.now() - datetime.timedelta(hours=age)
        # Obey a maximum age for artists if set.
        artists = Artist.objects.published()
        if age:
            artists = artists.filter(created__gte=earliest_date)
        query = Query()
        for artist in artists:
            time.sleep(1)  # Be nice to MusicBrainz.
            logger.debug('Searching for albums by %s.' % artist.name)
            # Find any official album release held by MusicBrainz for this
            # artist.
            filter = ReleaseFilter(artistName=artist.name,
                releaseTypes=(Release.TYPE_ALBUM, Release.TYPE_OFFICIAL))
            releases = query.getReleases(filter)
            logger.debug('Found %s albums.' % len(releases))
            for release in releases:
                album = release.release
                # Only import albums with an Amazon ASIN.  That allows for some
                # quality-control as Music Brainz lists every B-side and bonus
                # material you can think of.
                if album.asin:
                    # First try and find an already-existing album with this
                    # ASIN.  As an ASIN is unique it means we'll find it even
                    # if the fields have been changed since creation.
                    try:
                        db_album = Album.objects.get(asin=album.asin)
                        created = False
                    except Album.DoesNotExist:
                        # No album with that ASIN exists, so get or create an
                        # album with the same name by this artist.
                        db_album, created = Album.objects.get_or_create(
                            artist=artist, title=album.title)
                        db_album.asin = album.asin
                    # MusicBrainz stores releases dates for as many countries as
                    # it can.  I'm only interested in Britain though, so look
                    # for that first.  As a fallback, us the world wide release
                    # date (XE) or the US release date.
                    release_dates = dict((r.country, r.date)
                        for r in album.releaseEvents)
                    if (not db_album.release_date) and release_dates:
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
                    if not db_album.cover_art:
                        # Try and find the cover art on Last.fm.
                        logger.debug('Looking for cover art for %s ...' %
                            db_album.title)
                        album_id = unicodedata.normalize('NFKD', unicode(
                            ' '.join([artist.name, db_album.title]))).encode(
                            'ascii', 'ignore')
                        album_hash = hashlib.sha1(album_id).hexdigest()
                        lastfm = pylast.get_lastfm_network(
                            api_key=settings.LASTFM_API_KEY)
                        lastfm_album = lastfm.get_album(artist.name,
                            db_album.title)
                        try:
                            cover_image = lastfm_album.get_cover_image()
                            logger.debug('Reading image data from URL %s ...' % cover_image)
                            response = urllib2.urlopen(cover_image)
                            data = response.read()
                            # Store the photo on disk.
                            logger.debug('Saving photo to disk ...')
                            filename = os.path.join(settings.MEDIA_ROOT,
                                Album.PHOTO_UPLOAD_DIRECTORY,
                                '%s.jpg' % album_hash)
                            fh = open(filename, 'w')
                            fh.write(data)
                            fh.close()

                            # Link the photo to the album.
                            logger.info('Adding cover art to album %s by %s.'
                                % (db_album.title, artist.name))
                            db_album.cover_art = os.path.join(
                                Album.PHOTO_UPLOAD_DIRECTORY,
                                '%s.jpg' % album_hash)
                        except (pylast.WSError, AttributeError):
                            logger.debug('No cover art found.')
                        except urllib2.HTTPError:
                            logger.debug('HTTP error when retrieving cover art.')
                    if created:
                        logger.info('New album for %s: %s.' % (artist,
                            album.title))
                    db_album.save()

        logger.info('Import complete.')
