# core/urls.py
from django.http import HttpResponse
from django.urls import path

def home(request):
    return HttpResponse("SureJan is alive")

urlpatterns = [
    path("", home, name="home"),
]
