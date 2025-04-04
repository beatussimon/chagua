from django.http import HttpResponseServerError
from django.db import OperationalError

class DatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except OperationalError:
            return HttpResponseServerError("Database unavailable. Please try again later.")
        return response