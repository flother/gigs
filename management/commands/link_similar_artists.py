import logging
import logging.config

from django.conf import settings
from django.core.management.base import NoArgsCommand
import pylast

from gigs.models import Artist


class Command(NoArgsCommand):
    help = "Use Last.fm's API to link similar artists."

    def handle_noargs(self, **options):
        """
        Use the Last.fm API to link similar artists.  The similarity is
        based in listenership.
        """
        # Create the logger we'll use to store all the output.
        logging.config.fileConfig("logging.conf")
        logger = logging.getLogger('RippedRecordsLogger')
        logger.info('Linking similar artists.')
        # Create a connection to the Last.fm API.
        lastfm = pylast.get_lastfm_network(api_key=settings.LASTFM_API_KEY)
        # Loop through every published artist and look on Last.fm for similar
        # artists that are also in the system?
        for artist in Artist.objects.published():
            db_similar_artists = artist.similar_artists.published()
            try:
                lastfm_artist = lastfm.get_artist(artist.name)
                similar_artists = lastfm_artist.get_similar()
            except pylast.WSError:
                # Couldn't find the artist on Last.fm.
                continue
            for similar_artist in similar_artists:
                # Based on a little bit of research, a match of .25 or greater
                # seems to be a good benchmark for similarity.
                if similar_artist["match"] >= 0.25:
                    try:
                        db_similar_artist = Artist.objects.get(name=str(
                            similar_artist["item"]))
                        # If this is a new similar artist, add it to the set.
                        if db_similar_artist not in db_similar_artists:
                            artist.similar_artists.add(db_similar_artist)
                            logger.info("%s similar (%f) to %s." % (
                                db_similar_artist.name,
                                similar_artist["match"], artist))
                        # Make the reciprocal link if it doesn't exist.
                        if artist not in \
                                db_similar_artist.similar_artists.published():
                            db_similar_artist.similar_artists.add(artist)
                            logger.info("%s similar (%f) to %s." % (artist,
                                similar_artist["match"],
                                db_similar_artist.name))
                    except Artist.DoesNotExist:
                        pass
