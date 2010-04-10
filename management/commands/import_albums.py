import datetime
from optparse import make_option
import time

from django.core.management.base import BaseCommand

from gigs.models import Artist


class Command(BaseCommand):
    help = "Imports albums from MusicBrainz for all the artists in the database."
    base_options = (
        make_option('-a', '--age', action='store', default=0, type='int',
            help='Import albums only for those artists created within this time period (in hours). Default is all artists.'),
    )
    option_list = BaseCommand.option_list + base_options

    def handle(self, **options):
        """Import all released albums for each artist in the database."""
        artists = Artist.objects.published()
        # Obey a maximum age for artists if set.
        age = options.get('age', None)
        earliest_date = datetime.datetime.now() - datetime.timedelta(hours=age)
        if age:
            artists = artists.filter(created__gte=earliest_date)
        # Populate the artist's album set, pausing for one second after each
        # artist so we don't pummel the MusicBrainz and Last.fm APIs.
        for artist in artists:
            artist.populate_album_set()
            time.sleep(1)
