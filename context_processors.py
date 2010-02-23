from django.conf import settings


def amazon_affiliate_tag(request):
    """
    Add the project's Amazon affiliate tag to the template context, if it
    exists.
    """
    return {
        'AMAZON_AFFILIATE_TAG': getattr(settings, 'AMAZON_AFFILIATE_TAG', ''),
    }
