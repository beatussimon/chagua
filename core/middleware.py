from django.http import HttpResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = request.META.get('REMOTE_ADDR')
        key = f"rate-limit:{ip}"
        requests = cache.get(key, 0)
        if requests > 100:  # Example: 100 requests per minute
            # Use HttpResponse with status 429 instead of HttpResponseTooManyRequests
            return HttpResponse("Too Many Requests", status=429)
        cache.set(key, requests + 1, 60)  # Reset after 60 seconds
        return None