import logging
import os
import sys
import urllib2

from django.conf import settings
from django.core.management.base import NoArgsCommand
try:
    import pylast
except ImportError:
    pass

from gigs.models import Artist


LOGGING_VERBOSITY = {0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}


class Command(NoArgsCommand):
    help = "Attempt to find a photo, via the Last.fm API, for each artist without one."

    def handle_noargs(self, **options):
        """
        Attempt to find a photo for each Artist model object without one.
        The Last.fm API is used to find the primary image for each artist
        in their database.

        This requires the pylast module; if it isn't found the script will
        fail gracefully.
        """
        # Create the logger we'll use to store all the output.
        verbosity = int(options.get('verbosity', 1))
        logger = logging.getLogger('Ripped Records logger')
        logger.setLevel(LOGGING_VERBOSITY[verbosity])
        logger_handler = logging.StreamHandler()
        logger_formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        logger_handler.setFormatter(logger_formatter)
        logger.addHandler(logger_handler)

        # Make sure the pylast module is available.
        try:
            pylast
        except NameError:
            logger.critical('You need to install the pylast module.')
            sys.exit(1)

        # Create a connection to the Last.fm API.
        lastfm = pylast.get_lastfm_network(api_key=settings.LASTFM_API_KEY)
        # Make a call to the API for an image for each artist that doesn't yet
        # have a photo.
        artists = Artist.objects.filter(photo='')
        for artist in artists:
            logger.debug("Searching for a photo for %s ..." % artist.name)
            try:
                lastfm_artist = lastfm.get_artist(artist.name)
                lastfm_images = lastfm_artist.get_images()
                primary_image = lastfm_images[0]
                try:
                    primary_image_url = primary_image.sizes.original
                except AttributeError:
                    primary_image_url = primary_image['sizes']['original']
                logger.debug("Image found: %s." % primary_image_url)

                # Read the image data from the URL supplied.
                logger.debug('Reading image data from URL ...')
                response = urllib2.urlopen(primary_image_url)
                data = response.read()

                # Store the photo on disk.
                logger.debug('Saving photo to disk ...')
                filename = os.path.join(settings.MEDIA_ROOT,
                    Artist.PHOTO_UPLOAD_DIRECTORY, '%s.jpg' % artist.slug)
                fh = open(filename, 'w')
                fh.write(data)
                fh.close()

                # Link the photo to the artist (i.e. save the Artist object).
                logger.debug('Adding photo to artist ...')
                artist.photo = os.path.join(Artist.PHOTO_UPLOAD_DIRECTORY,
                    '%s.jpg' % artist.slug)
                artist.save()
                logger.info("Photo for %s added." % artist.name)
            except IndexError:
                logger.debug("No photo for %s." % artist.name)
            except pylast.WSError:
                logger.debug("Web service error for %s." % artist.name)
        logger.info('Import complete.')
