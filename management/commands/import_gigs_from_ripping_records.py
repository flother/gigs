import csv
import datetime
import logging
import logging.config
import re
import unicodedata
import urllib2

from django.conf import settings
from django.template.defaultfilters import slugify
from django.core.management.base import NoArgsCommand

from gigs.models import Gig, Artist, Venue, Town, Promoter, ImportIdentifier


CURRENT_YEAR = datetime.date.today().year
MONTHS = {
    'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4, 'MAY': 5, 'JUNE': 6,
    'JULY': 7, 'AUGUST': 8, 'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11,
    'DECEMBER': 12,
}
REVERSED_MONTHS = dict(zip(MONTHS.values(), MONTHS.keys()))
DATE_RE = re.compile(r'[a-z]{3} (?P<day>\d+)[a-z]{2}', re.IGNORECASE)
MONTH_RE = re.compile('^\*(?P<month>%s) .+\*$' %  '|'.join(MONTHS.keys()),
    re.IGNORECASE)
VENUE_AND_PROMOTER_RE = re.compile(
    r"^(?P<venue>.+?)"  # Venue.
    r"( (?P<town>[Edinburgh|Glasgow]+))?"  # Town.
    r"( (?P<promoter>[A-Z]{1,3}))?$"  # Promoter code.
)
PRICE_RE = re.compile(
    r"^\??(?P<price>\d{1,}\.\d{2})?"  # Price.
    r"(/\?\d{1,}\.\d{2})?"  # Second price; this is discarded.
    r" ?(?P<status>SOLD OUT|CANCELLED)?"  # "SOLD OUT" or "CANCELLED".
    r" ?(?P<info>.+?)?$"  # Extra information.
)


class RippedGig(object):

    """
    A gig taken from the Ripping Records site.  Fields include artist
    name, venue, town, promoter, ticket price, date, and additional info.

    The arguments are based on the columns found in the table on the
    Ripping Records site: http://rippingrecords.com/tickets01.html.

      * ``artist``: string with the name of the band, singer, etc
      * ``venue_and_promoter``: string in a format covered by
        ``VENUE_AND_PROMOTER_RE`` that holds the venue and promoter code.
      * ``date``: datetime.date object
      * ``price_and_info``: string containing the ticket price and any
        miscellaneous information in a format that can be handled by
        ``PRICE_RE``.
    """

    def __init__(self, artist, venue_and_promoter, date, price_and_info):
        self.artist = self._make_usable_string(artist)

        # Venue and promoter and stored in one cell so a regular
        # expression is used to separate the two.  Promoter won't always
        # appear.
        venue_and_promoter_match = VENUE_AND_PROMOTER_RE.match(
            self._make_usable_string(venue_and_promoter))
        self.venue = venue_and_promoter_match.group('venue')
        self.town = venue_and_promoter_match.group('town')
        self.promoter = venue_and_promoter_match.group('promoter')
        self.date = date

        # Price(s) and extra info are stored in one field, so they're
        # separated here.  There can be zero or more prices, and the
        # extra info doesn't always appear, but there will always be at
        # least one.
        price_and_info_match = PRICE_RE.match(self._make_usable_string(
            price_and_info))
        self.price = price_and_info_match.group('price')
        self.info = price_and_info_match.group('info')
        if price_and_info_match.group('status') == "SOLD OUT":
            self.sold_out = True
            self.cancelled = False
        elif price_and_info_match.group('status') == "CANCELLED":
            self.cancelled = True
            self.sold_out = False
        else:
            self.sold_out = False
            self.cancelled = False

    def __unicode__(self):
        return "%s at %s on %s" % (self.artist, self.venue, self.date)

    def _make_usable_string(self, str):
        """
        Convert to an ASCII string, removing any suspicious characters in
        the process.  This includes the asterisks added by Google Docs to
        indicate emphasis in the original HTML.
        """
        return unicodedata.normalize('NFKD', unicode(str)).encode('ascii',
            'ignore').strip('*')


class Command(NoArgsCommand):
    help = "Imports gigs from the Ripping Records web site via Google Docs."

    def handle_noargs(self, **options):
        """
        Get all the gigs listed on the Ripping Records web site and
        convert them all into usable data.

        Although the original data comes from the Ripping Records site the
        script uses a Google Docs spreadsheet's CSV output as an
        intermediate form, so Google does all the heavy lifting (i.e.
        screen-scraping the HTML).

        Original data: http://rippingrecords.com/tickets01.html.
        """
        # Create the logger we'll use to store all the output.
        logging.config.fileConfig("logging.conf")
        logger = logging.getLogger('RippedRecordsLogger')
        logger.info('Importing gigs from the Ripping Records spreadsheet.')

        # Get the CSV data from Google Docs.
        logger.debug('Retrieving data from Google Docs.')
        request = urllib2.Request(settings.RIPPING_RECORDS_SPREADSHEET_URL)
        request.add_header('User-Agent', 'Ripping Records scraper')
        ripping_data = urllib2.build_opener().open(request)
        logger.debug('Retrieved information.')

        # Current month holds the current month the gigs occur (the month is
        # given in a header row rather than in each row).
        current_month = 1
        # List of all included gigs.
        gigs = []

        # Parse the CSV data into individual gigs.  Each row is an individual
        # gig, although the month each gig takes place in is a header row.
        reader = csv.reader(ripping_data)
        for row in reader:
            if len(row) < 4:
                # If there are fewer than four columns in a row it's either a
                # header row indicating a new month, or blank or filled with
                # useless information.
                try:
                    month_match = MONTH_RE.match(row[0])
                    if month_match:
                        # Month has changed.
                        logger.debug('Month changed from %s to %s.' % (
                            REVERSED_MONTHS[current_month],
                            month_match.group('month')))
                        current_month = MONTHS[month_match.group('month')]
                    else:
                        # Text information we can safely ignore.
                        logger.debug("Unmatched row: '%s'." % ', '.join(row))
                except IndexError:
                    # Blank row.
                    logger.debug('Ignored blank row.')
            else:
                # If there are four columns it's probably a gig.  The only other
                # possibilities are if the first column is "*DATE*" (which means
                # it's a header row) or if all columns are "--" which means the
                # Google spreadsheet has fewer rows than last time (Google pads
                # it out).
                if not row[0] in ("*DATE*", "--"):
                    # Date of the gig based on the month header row we'll have
                    # come across earlier and the date column, which contains
                    # the day of month in a format like "mon 18th".
                    date = datetime.date(CURRENT_YEAR, current_month,
                        int(DATE_RE.match(row[0].strip('*')).group('day')))
                    # Create a gig based on this row.
                    logger.debug('Creating initial gig object.')
                    gigs.append(RippedGig(row[1], row[2], date, row[3]))

        # That's the import done.  Now let's convert all the gigs into lovely
        # Django models.
        for gig in gigs:
            logger.debug('Processing gig: %s at %s on %s.' % (gig.artist,
                gig.venue, gig.date))
            # Find or create the gig's artist.
            artist_id, created = ImportIdentifier.objects.get_or_create(
                identifier=gig.artist, type=ImportIdentifier.ARTIST_IMPORT_TYPE)
            try:
                artist = artist_id.artist_set.all()[0]
                logger.debug('Found artist: %s.' % artist)
            except IndexError:
                artist = Artist.objects.create(name=gig.artist,
                    slug=slugify(gig.artist)[:50])
                artist.import_identifiers.add(artist_id)
                artist.save()
                logger.info('Created artist: %s.' % artist)

            # Find or create the gig's town.  Occasionally this isn't included
            # in the Ripping Records table row for the gig.
            if gig.town:
                town_id, created = ImportIdentifier.objects.get_or_create(
                    identifier=gig.town, type=ImportIdentifier.TOWN_IMPORT_TYPE)
                try:
                    town = town_id.town_set.all()[0]
                    logger.debug('Found town: %s.' % town)
                except IndexError:
                    town = Town.objects.create(name=gig.town,
                        slug=slugify(gig.town)[:50])
                    town.import_identifiers.add(town_id)
                    town.save()
                    logger.info('Created town: %s.' % town)
            else:
                # Sometimes the town isn't included, so just assume it's
                # Edinburgh and change it manually later.
                town, created = Town.objects.get_or_create(name='Edinburgh')
                logger.debug('No town listed for gig; using default.')

            # Find or create the gig's venue.
            venue_id, created = ImportIdentifier.objects.get_or_create(
                identifier=gig.venue, type=ImportIdentifier.VENUE_IMPORT_TYPE)
            try:
                venue = venue_id.venue_set.all()[0]
                logger.debug('Found venue: %s.' % venue)
            except IndexError:
                venue = Venue.objects.create(name=gig.venue,
                    slug=slugify(gig.venue)[:50], town=town)
                venue.import_identifiers.add(venue_id)
                venue.save()
                logger.info('Created venue: %s.' % venue)

            # Find or create the promoter. The promoter isn't always listed for
            # a gig, so only create it exists.
            promoter = None
            if gig.promoter:
                promoter_id, created = ImportIdentifier.objects.get_or_create(
                    identifier=gig.promoter,
                    type=ImportIdentifier.PROMOTER_IMPORT_TYPE)
                try:
                    promoter = promoter_id.promoter_set.all()[0]
                    logger.debug('Found promoter: %s.' % promoter)
                except IndexError:
                    promoter = Promoter.objects.create(name=gig.promoter,
                        slug=slugify(gig.promoter)[:50])
                    promoter.import_identifiers.add(promoter_id)
                    promoter.save()
                    logger.info('Created promoter: %s.' % promoter)
            else:
                logger.debug('No promoter found.')

            # Return a unique identifier for this gig, based on the artist,
            # venue, and date.
            gig_identifier = '%s at %s on %s' % (gig.artist, gig.venue,
                gig.date)
            # Find or create the gig.
            gig_id, created = ImportIdentifier.objects.get_or_create(
                identifier=gig_identifier,
                type=ImportIdentifier.GIG_IMPORT_TYPE)
            try:
                db_gig = gig_id.gig_set.all()[0]
                logger.debug('Gig already exists.')
                # If the gig already exists make sure it's marked appropriately
                # as sold out, cancelled, or not.
                if not db_gig.sold_out == gig.sold_out:
                    db_gig.sold_out = gig.sold_out
                    db_gig.save()
                    logger.debug("Updated the gig's sold out flag.")
                if not db_gig.cancelled == gig.cancelled:
                    db_gig.cancelled = gig.cancelled
                    db_gig.save()
                    logger.debug("Updated the gig's cancelled flag.")
            except IndexError:
                # Check to see if a gig by the same artist is already
                # happening on the same day in a different venue.  If there
                # is, this new gig is likely to be that gig at a changed
                # venue.
                try:
                    db_gig = Gig.objects.exclude(venue=venue).get(
                        artist=artist, date=gig.date)
                    logger.info('Gig changed venue: %s -> %s' % (db_gig, venue))
                    db_gig.promoter = promoter
                    db_gig.price = gig.price
                    db_gig.sold_out = gig.sold_out
                    db_gig.cancelled = gig.cancelled
                    info_string = "Venue changed from %s to %s." % (
                        db_gig.venue.name, venue.name)
                    if gig.info:
                        db_gig.extra_information = "%s. %s" % (gig.info,
                            info_string)
                    else:
                        db_gig.extra_information = info_string
                    db_gig.venue = venue
                except Gig.DoesNotExist:
                    # This is definitely a new gig we have here.
                    db_gig = Gig.objects.create(artist=artist, slug=artist.slug,
                        venue=venue, promoter=promoter, date=gig.date,
                        price=gig.price, sold_out=gig.sold_out,
                        cancelled=gig.cancelled, extra_information=gig.info)
                    logger.info('Gig created: %s.' % db_gig)
                db_gig.import_identifiers.add(gig_id)
                db_gig.save()
        logger.info('Import complete.')
        # Finally, save every Artist, Venue, Town, and Promoter object.  This is
        # a brute-force way of making sure every object's
        # ``number_of_upcoming_gigs`` field is correct and up-to-date.
        logger.debug('Saving all models to update the number of upcoming gigs.')
        for model in [Artist, Venue, Town, Promoter]:
            for obj in model.objects.all():
                obj.save(update_number_of_upcoming_gigs=True)
        logger.info('All model objects updated.')
