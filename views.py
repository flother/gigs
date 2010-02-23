import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

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

    # Create four lists: the eight gigs happening soonest, gigs happening this
    # week (Monday to Sunday; ignoring days already passed), gigs happening next
    # week (Monday to Sunday), and the 15 gigs most recently added to the
    # database.
    closest_gigs = Gig.objects.published(date__gte=today,
        sold_out=False).select_related()[:8]
    gigs_this_week = Gig.objects.published(date__gte=today,
        date__lt=start_of_next_week).select_related()
    gigs_next_week = Gig.objects.published(date__gte=start_of_next_week,
        date__lt=start_of_week_after_next).select_related()
    new_gigs = Gig.objects.published(date__gte=today).order_by(
        '-created').select_related()[:15]

    # Create lists of artists and venues, those with the largest number of
    # upcoming gigs first, all towns, and the number of gigs at each venue and
    # for each artist.
    artists = Artist.objects.filter(number_of_upcoming_gigs__gt=0).order_by(
        '-number_of_upcoming_gigs', '?')[:17]
    number_of_artists = Artist.objects.count()
    venues = Venue.objects.filter(number_of_upcoming_gigs__gt=0).order_by(
        '-number_of_upcoming_gigs')[:11]
    number_of_venues = Venue.objects.count()
    towns = Town.objects.filter(number_of_upcoming_gigs__gt=0)
    number_of_towns = Town.objects.count()

    upcoming_months_with_gigs = Gig.objects.published(date__gte=today).dates(
        'date', 'month')[:8]

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


def artist_list(request):
    """List all artists by name."""
    earliest_gig = Gig.objects.published()[0]

    # Create an empty dictionary with upper-case letters of the alphabet as
    # keys and empty lists as values.  The lists will be filled with artists
    # according to the first letter of their name.  Any band not starting with a
    # letter of the Latin alphabet is added to '#'.
    alphabet = ['#'] + map(chr, range(65, 91))
    alphabetic_artists = dict((letter, []) for letter in alphabet)
    artists = Artist.objects.all()
    for artist in artists:
        first_letter = artist.name[0].upper()
        if not first_letter in alphabet:
            first_letter = '#'
        alphabetic_artists[first_letter].append(artist)

    context = {
        'earliest_gig': earliest_gig,
        'alphabetic_artists': alphabetic_artists,
        'artist_count': len(artists),
    }
    return render_to_response('gigs/artist_list.html', context,
        RequestContext(request))


def artist_detail(request, slug):
    today = datetime.date.today()
    artist = get_object_or_404(Artist, slug=slug)
    upcoming_gigs = Gig.objects.published(date__gte=today)
    past_gigs = Gig.objects.published(date__lt=today)

    context = {
        'artist': artist,
        'upcoming_gigs': upcoming_gigs,
        'past_gigs': past_gigs,
    }
    return render_to_response('gigs/artist_detail.html', context,
        RequestContext(request))


def venue_list(request):
    """List all venues by name, categorised by town."""
    town_list = Town.objects.all().select_related()
    context = {
        'town_list': town_list,
    }
    return render_to_response('gigs/venue_list.html', context,
        RequestContext(request))
