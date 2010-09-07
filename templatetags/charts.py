import datetime

from django.conf import settings
from django.db.models import Count
from django import template

from gigs.models import Gig


register = template.Library()
GOOGLE_CHARTS_URL = "http://chart.apis.google.com/chart"


@register.simple_tag
def upcoming_gigs_sparkline_url():
    """
    Returns the URL to display a Google Charts graph showing the number
    of upcoming gigs on the site by day.  Defaults to a 940x21 pixel
    sparkline but the chart settings can be overridden by defining a
    dictionary named GOOGLE_CHARTS_OPTIONS in the project's settings.
    """
    today = datetime.date.today()
    gig_dates = Gig.objects.published(date__gte=today).values(
        "date").order_by().annotate(Count("date"))
    dates = {}
    for date in gig_dates:
        dates[date["date"]] = date["date__count"]
    chart_values = []
    last_date = gig_dates[len(dates) - 1].values()[0]
    for addition in range((last_date - today).days + 1):
        next_date = today + datetime.timedelta(days=addition)
        if dates.has_key(next_date):
            chart_values.append(dates[next_date])
        else:
            chart_values.append(0)

    chart_options = {
        "cht": "ls",
        "chs": "940x21",
        "chd": "t:" + ",".join(map(str, chart_values)),
        "chds": "0,%d" % max(chart_values),
    }
    chart_options.update(getattr(settings, "GOOGLE_CHARTS_OPTIONS", {}))
    return "%s?%s" % (GOOGLE_CHARTS_URL, "&".join(["=".join([k, v])
        for k, v in chart_options.items()]))
