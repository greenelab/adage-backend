try:
    from django.conf import settings
except ImportError:
    settings = {}

TRIBE_URL = getattr(settings, 'TRIBE_URL', 'https://tribe.greenelab.com')

CROSSREF = getattr(settings, 'TRIBE_CROSSREF_DB', 'Entrez')

TRIBE_ID = getattr(settings, 'TRIBE_ID', '')
TRIBE_SECRET = getattr(settings, 'TRIBE_SECRET', '')

TRIBE_REDIRECT_URI = getattr(settings, 'TRIBE_REDIRECT_URI', '')

TRIBE_LOGIN_REDIRECT = getattr(settings, 'TRIBE_LOGIN_REDIRECT', None)
TRIBE_LOGOUT_REDIRECT = getattr(settings, 'TRIBE_LOGOUT_REDIRECT', None)

ACCESS_CODE_URL = TRIBE_URL + '/oauth2/authorize/'
ACCESS_TOKEN_URL = TRIBE_URL + '/oauth2/token/'

TRIBE_SCOPE = getattr(settings, 'TRIBE_SCOPE', 'read')

BASE_TEMPLATE = getattr(settings, 'TRIBE_CLIENT_BASE_TEMPLATE', 'base.html')

PUBLIC_GENESET_FOLDER = getattr(settings, 'PUBLIC_GENESET_FOLDER', None)

MAX_GENES_IN_PGENESETS = getattr(settings, 'MAX_GENES_IN_PGENESETS', 300)
