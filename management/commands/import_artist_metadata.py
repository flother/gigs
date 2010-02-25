import datetime
import logging
from optparse import make_option
import sys
import time
import urllib2

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.html import strip_tags
import pylast

from gigs.models import Artist


LOGGING_VERBOSITY = {0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}


class Command(BaseCommand):
    help = "Import metadata (currently just biographies) for all artists."
    base_options = (
        make_option('-a', '--age', action='store', default=0, type='int',
            help='Import metadata only for those artists created within this time period (in hours). Default is all artists.'),
    )
    option_list = BaseCommand.option_list + base_options

    def handle(self, **options):
        """
        Import artist metadata from Last.fm.

        Currently the only metadata that's imported is an artist's biography,
        but more may be imported in the future.
        """
        # Create the logger we'll use to store all the output.
        verbosity = int(options.get('verbosity', 1))
        logger = logging.getLogger('Ripped Records logger')
        logger.setLevel(LOGGING_VERBOSITY[verbosity])
        logger_handler = logging.StreamHandler()
        logger_formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        logger_handler.setFormatter(logger_formatter)
        logger.addHandler(logger_handler)
        logger.info('Importing artist metadata.')

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
        artists = Artist.objects.all()
        if age:
            artists = artists.filter(created__gte=earliest_date)
        # Loop through each artist.
        for artist in artists:
            time.sleep(1)  # Be nice to Last.fm.
            logger.debug('Searching for metadata for %s.' % artist.name)
            # Open a connection to the Last.fm API.
            lastfm = pylast.get_lastfm_network(api_key=settings.LASTFM_API_KEY)
            lastfm_artist = lastfm.get_artist(artist.name)
            try:
                # Get the biography and the date it was published from Last.fm.
                biography = lastfm_artist.get_bio_content()
                bio_published_date = lastfm_artist.get_bio_published_date()
                if bio_published_date:
                    date_biography_updated = datetime.datetime(*time.strptime(
                        bio_published_date, "%a, %d %b %Y %H:%M:%S +0000")[:6])
                    plain_text_biography = strip_tags(biography)
                    # If the Last.fm biography has been updated since this
                    # artist was last saved, and the biography is different to
                    # the saved version, OR the artist biography is blank, save
                    # the artist's biography.
                    if ((not plain_text_biography == artist.biography) and
                            (date_biography_updated > artist.updated or
                            artist.biography == '')):
                        artist.biography = plain_text_biography
                        artist.save()
                        logger.info("Saved biography for %s" % artist.name)
            except (pylast.WSError, urllib2.URLError, urllib2.HTTPError):
                # An error occurs if the artist's name has a character in that
                # Last.fm doesn't like, or on the occasional dropped connection.
                logger.debug("Error with %s" % artist.name)

        logger.info('Artist metadata import complete.')
