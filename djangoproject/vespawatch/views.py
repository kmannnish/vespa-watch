from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from .models import Observation


def index(request):
    return render(request, 'vespawatch/index.html')


class ObservationCreate(CreateView):
    model = Observation
    template_name = 'vespawatch/observation_add_form.html'
    fields = ('species', 'subject', 'nest_location', 'latitude', 'longitude', 'inaturalist_id', 'observation_time',
              'comments')

class ObservationUpdate(UpdateView):
    model = Observation
    template_name = 'vespawatch/observation_update_form.html'
    fields = ('species', 'subject', 'nest_location', 'latitude', 'longitude', 'inaturalist_id', 'observation_time',
              'comments')

class ObservationDelete(DeleteView):
    model = Observation
    success_url = reverse_lazy('vespawatch:index')

# ==============
# API methods
# ==============

def observations_json(request):
    """
    Return all observations as json data
    """
    observations = Observation.objects.all()
    return JsonResponse({
        'observations': [x.as_dict() for x in observations]
    })
