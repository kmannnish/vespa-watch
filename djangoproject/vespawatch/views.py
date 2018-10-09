from django.shortcuts import render
from django.http import JsonResponse
from .models import Observation

def index(request):
    return render(request, 'vespawatch/index.html')


def observations_json(request):
    observations = Observation.objects.all()
    return JsonResponse({
        'observations': [x.as_dict() for x in observations]
    })
