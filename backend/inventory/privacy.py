from django.utils.cache import patch_cache_control, patch_vary_headers
from django.utils.deprecation import MiddlewareMixin


class ApiPrivacyMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path_info.startswith('/api/'):
            if 'no-store' not in response.get('Cache-Control', '').lower():
                patch_cache_control(response, private=True, no_store=True, no_cache=True, max_age=0)
            patch_vary_headers(response, ['Cookie'])
        return response
