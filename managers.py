import datetime
from django.db.models import Manager


class PublishedManager(Manager):

    """
    Django model manager for any model with a ``published`` BooleanField.
    Overrides the default ``latest()`` method so it returns the latest
    published object, and adds a ``published()`` method that returns only
    published objects.
    """

    def latest(self, field_name=None):
        """Return the latest published object."""
        return self.published().latest(field_name)

    def published(self, **kwargs):
        """
        Return a ``QuerySet`` that contains only those objects deemed fit
        to publish, i.e. objects where the ``published`` field is
        ``True``.
        """
        return self.get_query_set().filter(published=True, **kwargs)
