from django.shortcuts import render
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.views import generic
# Create your views here.


def homepage(request):
    return render (request, 'home/homepage.html')