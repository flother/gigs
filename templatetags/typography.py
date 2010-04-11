from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
@stringfilter
def truncate(value, max_length=15):
    """
    Return a string, truncated if it exceeds the ``max_length`` argument
    in length.  If truncated, the string will be ``max_length`` characters
    long, the last being a horizontal ellipsis.  If no truncation was
    necessary the original string is returned.

    >>> truncate('123456789012345')
    '123456789012345'
    >>> truncate('1234567890123456')
    '12345678901234\u2026'
    >>> truncate('This is a long sentence, with nothing to say')
    u'This is a long\u2026'
    >>> truncate('This is a long sentence, with nothing to say', 26)
    u'This is a long sentence,\u2026'
    """
    if len(value) > max_length:
        return value[:max_length - 1].strip() + u'\u2026'
    else:
        return value
