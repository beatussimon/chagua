from django.http import HttpResponseTooManyRequests
from django.core.cache import cache

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            key = f"rate_limit_{request.user.id}"
            requests = cache.get(key, 0)
            if requests > 100:  # 100 requests per minute
                return HttpResponseTooManyRequests("Too many requests.")
            cache.set(key, requests + 1, 60)
        return self.get_response(request)