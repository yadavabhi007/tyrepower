from django.shortcuts import HttpResponse, render


class UnderConstructionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = render(request, 'tyrepower_app/under-construction.html')
        return response