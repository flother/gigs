import datetime
from django.db.models import Manager


class GigManager(Manager):

    """
    Django model manager for the ``Gig`` model. Overrides the default
    ``latest()`` method so it returns the latest published gig, and adds a
    ``published()`` method that returns only published gigs.
    """

    def latest(self, field_name=None):
        """Return the latest published gig."""
        return self.published().latest(field_name)

    def published(self, **kwargs):
        """
        Return a ``QuerySet`` that contains only those gigs deemed fit
        to publish, i.e. gigs where the ``published`` field is ``True``.
        """
        from gigs.models import Gig
        return self.get_query_set().filter(published=True, **kwargs)
