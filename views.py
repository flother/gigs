import base64
import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.views.generic.simple import redirect_to

from gigs.models import Gig, Artist, Venue, Town


def home_page(request):
    """
    Lots of lovely lists to give the visitor an idea of what's happening
    soon and how they can browse the site.

    The view provides the template with the eight soonest occurring gigs,
    gigs happening this week and next, the fifteen most recently added
    gigs, and artists, venues, and towns.
    """
    today = datetime.date.today()
    one_week = datetime.timedelta(days=7)
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    start_of_next_week = start_of_this_week + one_week
    start_of_week_after_next = start_of_next_week + one_week

    # Create four lists: the eight gigs happening soonest (minus those that are
    # sold out and whose artist doesn't have a photo), gigs happening this week
    # (Monday to Sunday; ignoring days already passed), gigs happening next
    # week (Monday to Sunday), and the 15 gigs most recently added to the
    # database.
    closest_gigs = Gig.objects.upcoming(sold_out=False).exclude(
        artist__photo='').select_related()[:8]
    gigs_this_week = Gig.objects.upcoming(
        date__lt=start_of_next_week).select_related()
    gigs_next_week = Gig.objects.published(date__gte=start_of_next_week,
        date__lt=start_of_week_after_next).select_related()
    new_gigs = Gig.objects.upcoming().order_by('-created').select_related()[:15]

    # Create lists of artists and venues, those with the largest number of
    # upcoming gigs first, all towns, and the number of gigs at each venue and
    # for each artist.
    artists = Artist.objects.published(number_of_upcoming_gigs__gt=0).order_by(
        '-number_of_upcoming_gigs', '?')[:17]
    number_of_artists = Artist.objects.count()
    venues = Venue.objects.published(number_of_upcoming_gigs__gt=0).order_by(
        '-number_of_upcoming_gigs')[:11]
    number_of_venues = Venue.objects.count()
    towns = Town.objects.published(number_of_upcoming_gigs__gt=0)
    number_of_towns = Town.objects.count()

    upcoming_months_with_gigs = Gig.objects.upcoming().dates('date', 'month')[:8]

    context = {
        'closest_gigs': closest_gigs,
        'gigs_this_week': gigs_this_week,
        'gigs_next_week': gigs_next_week,
        'new_gigs': new_gigs,
        'artists': artists,
        'venues': venues,
        'towns': towns,
        'number_of_artists': number_of_artists,
        'number_of_venues': number_of_venues,
        'number_of_towns': number_of_towns,
        'upcoming_months_with_gigs': upcoming_months_with_gigs,
    }
    return render_to_response('gigs/home_page.html', context,
        RequestContext(request))


def gigs_archive(request):
    """
    List all upcoming gigs, soonest first, and a list of months (by year) that
    gigs have or will occur in.
    """
    months_with_gigs = Gig.objects.published().order_by('-date').dates('date',
        'month')
    upcoming_gigs = Gig.objects.upcoming().select_related()
    context = {
        'months_with_gigs': months_with_gigs,
        'upcoming_gigs': upcoming_gigs,
    }
    return render_to_response('gigs/gig_archive.html', context,
        RequestContext(request))


def gig_detail(request, year, month, day, slug):
    """Display the details of one particular gig."""
    gig_date = datetime.date(*map(int, [year, month, day]))
    gig = get_object_or_404(Gig.objects.published().select_related(),
        date=gig_date, slug=slug)
    context = {
        'gig': gig,
    }
    return render_to_response('gigs/gig_detail.html', context,
        RequestContext(request))


def gig_detail_shorturl(request, base32_id):
    """
    Return a permanent redirect (HTTP 301) to a gig's absolute URL using
    the gig's id in base32.
    """
    # Pad the base32 id out to a length divisible by 8, as required by the
    # base64 library.
    base32_id += '=' * (8 % len(base32_id))
    id = base64.b32decode(base32_id, casefold=True)
    gig = get_object_or_404(Gig, pk=id)
    return redirect_to(request, gig.get_absolute_url())


def artist_list(request):
    """List all artists by name."""
    # Create an empty dictionary with upper-case letters of the alphabet as
    # keys and empty lists as values.  The lists will be filled with artists
    # according to the first letter of their name.  Any band not starting with a
    # letter of the Latin alphabet is added to '#'.
    alphabet = ['#'] + map(chr, range(65, 91))
    alphabetic_artists = SortedDict()
    for letter in alphabet:
        alphabetic_artists[letter] = []
    artists = Artist.objects.published()
    for artist in artists:
        first_letter = artist.slug[0].upper()
        if not first_letter in alphabet:
            first_letter = '#'
        alphabetic_artists[first_letter].append(artist)

    context = {
        'alphabetic_artists': alphabetic_artists,
        'artist_count': len(artists),
    }
    return render_to_response('gigs/artist_list.html', context,
        RequestContext(request))


def venue_list(request):
    """List all venues by name, categorised by town."""
    town_list = Town.objects.published().select_related()
    context = {
        'town_list': town_list,
    }
    return render_to_response('gigs/venue_list.html', context,
        RequestContext(request))
