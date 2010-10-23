# encoding: utf-8
import datetime
import logging
import logging.config
try:
    import json
except ImportError:
    import simplejson as json
import urllib
import urllib2

from django.conf import settings
from django.core.management.base import BaseCommand

from gigs.models import Artist, Review


__all__ = ("Command",)
OPENPLATFORM_API_END_POINT = "http://content.guardianapis.com/search"


API_PARAMETERS = {
    "api-key": settings.OPENPLATFORM_API_KEY,
    "section": "music",
    "tag": "tone/reviews",
    "page-size": 50,
    "order-by": "oldest",
    "format": "json",
    "show-fields": "headline,byline,trail-text,star-rating",
    "show-references": "musicbrainz",
    "reference-type": "musicbrainz",
}


def api_url(page, from_date=None, **kwargs):
    """
    Builds a URL for the Open Platform API that will return review
    results.
    """
    api_params = API_PARAMETERS.copy()
    api_params.update(kwargs)
    page_parameters = {
        "page": page,
    }
    if from_date:
        page_parameters["from-date"] = from_date.strftime("%Y-%m-%d")
    api_params.update(page_parameters)
    return "%s?%s" % (OPENPLATFORM_API_END_POINT,
        urllib.urlencode(api_params))


def save_review(review):
    """
    Saves a Guardian review if there's a MusicBrainz id that matches an
    artist in the database and the review has a rating out of five.
    Returns ``True`` if the review was saved, ``False`` otherwise.
    """
    # Get the useful fields.  Note that not all these are mandatory.
    external_id = review.get("id")
    headline = review["fields"]["headline"]
    url = review["webUrl"]
    byline = review["fields"].get("byline", "")
    trail = review["fields"].get("trailText", "")
    try:
        rating = review["fields"]["starRating"]
    except KeyError:
        # If there's no rating, ignore this review.
        return False
    # Remove the crud from the headline.
    if headline.endswith(u" – review") or headline.endswith(u" - review"):
        headline = headline[:-9]
    # Convert the date string to a datetime.datetime object.
    date_string = review["webPublicationDate"]
    # Split the timezone from the time and date.
    date_parts = date_string.rsplit("+", 1)
    time = date_parts[0]
    # Use the timezone to convert it to UTC if there is one.
    if len(date_parts) == 2:
        tz = date_parts[1]
        # Split the timezone offset from UTC into hours and minutes.
        tz = tz.split(":")
        # Create a datetime.datetime object with the correct offset from
        # UTC.  This means all times are UTC.
        tz = datetime.timedelta(hours=int(tz[0]), minutes=int(tz[1]))
        date = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S') + tz
    else:
        date = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    # Find the MusicBrainz id.
    for reference in review["references"]:
        if reference["type"] == "musicbrainz":
            musicbrainz_id = reference["id"].rsplit("/", 1)[1]
            try:
                artist = Artist.objects.get(mbid=musicbrainz_id)
                # Does this review exist in the database?
                try:
                    Review.objects.get(external_id=external_id)
                except Review.DoesNotExist:
                    review = Review(external_id=external_id,
                        publication_date=date, headline=headline,
                        trail=trail, byline=byline, url=url, artist=artist,
                        rating=rating)
                    review.save()
                    return True
            except Artist.DoesNotExist:
                pass
    return False


class Command(BaseCommand):
    help = "Imports artist reviews from the Guardian."

    def handle(self, **options):
        """
        Import all Guardian reviews with ratings for each artist in the
        database.  The reviews are handled in two parts.  First, reviews
        published after the most recent review in the database (or all
        reviews if the database is empty) are retrieved from the
        Guardian API.

        Second, all reviews for artists created in the last two days are
        retrieved.  This second stage is to allow older reviews for new
        artists to be collected -- without it reviews for new artists
        would only be stored that were written after they were created.

        If it's not obvious from the wonderful description, this command
        needs to be run at least once every two days to ensure all
        reviews are discovered.
        """
        # Create the logger we'll use to store all the output.
        logging.config.fileConfig("logging.conf")
        logger = logging.getLogger('RippedRecordsLogger')
        logger.info('Importing reviews from the Guardian.')
        # Only look for reviews newer than the latest one in the database, if
        # there is one.
        try:
            earliest_review_date = Review.objects.all()[0].publication_date
            logger.debug("Earliest review date: %s." % earliest_review_date)
        except IndexError:
            earliest_review_date = None
            logger.debug("No earliest date set; retrieving all reviews.")
        # Get the first page of reviews.
        logger.debug("Retrieving reviews page 1.")
        first_page = json.loads(urllib2.urlopen(api_url(1,
            earliest_review_date)).read())
        number_of_pages = int(first_page["response"]["pages"])
        logger.debug("API indicates %d pages in total." % number_of_pages)
        saved_reviews = 0
        for review in first_page["response"]["results"]:
            if save_review(review):
                saved_reviews += 1
        # Get reviews on page 2 of the API results onwards.
        page_range = range(2, number_of_pages + 1)
        for page in page_range:
            logger.debug("Retrieving reviews page %d." % page)
            found_page = False
            while not found_page:
                try:
                    page = json.loads(urllib2.urlopen(api_url(page,
                        earliest_review_date)).read())
                    found_page = True
                except urllib2.HTTPError:
                    # If the page couldn't be retrieved for any reason, retry.
                    # This is pretty brute force -- it'll loop for a long time
                    # if the API limit has been reached for example -- but it
                    # should do for our needs.
                    pass
            for review in page["response"]["results"]:
                saved_reviews += save_review(review)
        logger.info("Saved %d new reviews." % saved_reviews)

        # Now we need to get old reviews for artists created after the latest
        # review date.
        if earliest_review_date:
            earliest_artist_creation = (datetime.datetime.today() -
                datetime.timedelta(days=2))
            artists = Artist.objects.published(
                created__gte=earliest_artist_creation).exclude(mbid="")
            logger.info("%d artists created within the last two days." % len(
                artists))
            for artist in artists:
                artist_api_url = api_url(page=1,
                    reference="musicbrainz/%s" % artist.mbid)
                found_page = False
                while not found_page:
                    try:
                        page = json.loads(urllib2.urlopen(
                            artist_api_url).read())
                        found_page = True
                        artist_reviews = 0
                        for review in page["response"]["results"]:
                            artist_reviews += save_review(review)
                        logger.info("Saved %d reviews for %s." % (
                            artist_reviews, artist.name))
                    except urllib2.HTTPError:
                        # If the page couldn't be retrieved for any reason,
                        # retry.  This is pretty brute force -- it'll loop
                        # for a long time if the API limit has been reached for
                        # example -- but it should do for our needs.
                        pass
