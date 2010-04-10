import datetime
from optparse import make_option
import time

from django.core.management.base import BaseCommand

from gigs.models import Artist


class Command(BaseCommand):
    help = "Import metadata (photo and biography) for all artists."
    base_options = (
        make_option('-a', '--age', action='store', default=0, type='int',
            help='Import metadata only for those artists created within this time period (in hours). Default is all artists.'),
    )
    option_list = BaseCommand.option_list + base_options

    def handle(self, **options):
        """
        Import artist metadata from Last.fm.

        Currently the only metadata that's imported is an artist's photo and
        biography, but more may be imported in the future.
        """
        artists = Artist.objects.published()
        # Obey a maximum age for artists if set.
        age = options.get('age', 0)
        earliest_date = datetime.datetime.now() - datetime.timedelta(hours=age)
        if age:
            artists = artists.filter(created__gte=earliest_date)
        # Loop through each artist, pausing for one second after each
        # artist so we don't pummel the Last.fm API.
        for artist in artists:
            artist.get_photo()
            artist.get_biography()
            time.sleep(1)
