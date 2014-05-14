from django.conf import settings
import os

def site_settings(request):

    site_info = {
        'SITE_URL': getattr(settings, 'SITE_URL', '/'),
        'SITE_NAME': getattr(settings, 'SITE_NAME', os.path.split(os.path.dirname(__file__))[-1]),
    }

    return site_info