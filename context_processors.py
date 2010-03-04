from django.conf import settings


def amazon_affiliate_tag(request):
    """
    Add the project's Amazon affiliate tag to the template context, if it
    exists.
    """
    return {
        'AMAZON_AFFILIATE_TAG': getattr(settings, 'AMAZON_AFFILIATE_TAG', ''),
    }


def cloudmade(request):
    """
    Adds the project's Cloudmade API key and style id into the template
    context.
    """
    return {
        'CLOUDMADE_API_KEY': getattr(settings, 'CLOUDMADE_API_KEY', ''),
        'CLOUDMADE_STYLE_ID': getattr(settings, 'CLOUDMADE_STYLE_ID', '')
    }
