from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.utils.deprecation import MiddlewareMixin

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = request.META.get('REMOTE_ADDR')
        key = f"ratelimit:{ip}"
        requests = cache.get(key, 0)
        if requests >= 100:  # 100 requests per minute
            return HttpResponseTooManyRequests("Too many requests")
        cache.set(key, requests + 1, 60)
        return None