import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext

from gigs.models import Gig


def home_page(request):
    """
    Show lists of gigs happening this week and the week after.  It also
    includes the eight soonest occurring gigs in a separate list, along
    with the fifteen most recently added gigs.
    """
    today = datetime.date.today()
    one_week = datetime.timedelta(days=7)
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    start_of_next_week = today + one_week
    start_of_week_after_next = start_of_next_week + one_week

    closest_gigs = Gig.objects.published(date__gte=today).select_related()[:8]
    gigs_this_week = Gig.objects.published(date__gte=today,
        date__lt=start_of_next_week).select_related()
    gigs_next_week = Gig.objects.published(date__gte=start_of_next_week,
        date__lt=start_of_week_after_next).select_related()
    new_gigs = Gig.objects.published(date__gte=today).order_by(
        '-created').select_related()[:15]

    context = {
        'closest_gigs': closest_gigs,
        'gigs_this_week': gigs_this_week,
        'gigs_next_week': gigs_next_week,
        'new_gigs': new_gigs,
    }
    return render_to_response('gigs/home_page.html', context,
        RequestContext(request))
