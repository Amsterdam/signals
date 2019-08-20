from django.conf import settings

SIGNALS_API_MAX_UPLOAD_SIZE = 8388608  # 8MB = 8*1024*1024
SIGNALS_API_ATLAS_SEARCH_URL = settings.DATAPUNT_API_URL + 'atlas/search'
